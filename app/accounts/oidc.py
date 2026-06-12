"""Authentik OIDC authentication backend (V6).

Authentik answers "who is this user and can they access Melodu?";
this backend turns the OIDC claims into a local Django user so audit logs,
cashier attribution, and the StaffProfile role system keep working unchanged.
"""
import logging

from django.conf import settings
from mozilla_django_oidc.auth import OIDCAuthenticationBackend

from audit.models import AuditLog
from audit.services import create_audit_log
from core.permissions import (
    ROLE_CASHIER,
    ROLE_INVENTORY,
    ROLE_MANAGER,
    ROLE_OWNER,
    ROLE_VIEWER,
)

from .models import StaffProfile

logger = logging.getLogger(__name__)

MODULE = "accounts"

# Authentik group → StaffProfile role, strongest first. A user in several
# melodu-* groups gets the highest role in this list.
AUTHENTIK_GROUP_ROLE_MAP = (
    ("melodu-admin", ROLE_OWNER),
    ("melodu-manager", ROLE_MANAGER),
    ("melodu-inventory", ROLE_INVENTORY),
    ("melodu-cashier", ROLE_CASHIER),
    ("melodu-report-viewer", ROLE_VIEWER),
)


def role_from_authentik_groups(group_names):
    names = {str(name).strip().lower() for name in group_names}
    for group_name, role in AUTHENTIK_GROUP_ROLE_MAP:
        if group_name in names:
            return role
    return None


class MeloduOIDCBackend(OIDCAuthenticationBackend):
    def authenticate(self, request, **kwargs):
        user = super().authenticate(request, **kwargs)
        if user is not None and not user.is_active:
            logger.warning("OIDC login denied for inactive user '%s'.", user.username)
            create_audit_log(
                action=AuditLog.Action.LOGIN_FAILED,
                module=MODULE,
                request=request,
                object_type="User",
                object_id=user.pk,
                object_display=user.username,
                new_value={"denied": "inactive", "source": "oidc"},
            )
            return None
        return user

    def get_username(self, claims):
        return (
            claims.get("preferred_username")
            or claims.get("email")
            or super().get_username(claims)
        )

    def verify_claims(self, claims):
        # Email may legitimately be missing for staff accounts; any stable
        # identifier is enough to map the login to a local user.
        return bool(claims.get("preferred_username") or claims.get("email") or claims.get("sub"))

    def filter_users_by_claims(self, claims):
        username = claims.get("preferred_username", "").strip()
        if username:
            users = self.UserModel.objects.filter(username__iexact=username)
            if users.exists():
                return users
        email = claims.get("email", "").strip()
        if email:
            return self.UserModel.objects.filter(email__iexact=email)
        return self.UserModel.objects.none()

    def create_user(self, claims):
        username = self.get_username(claims)
        user = self.UserModel.objects.create_user(
            username=username,
            email=claims.get("email", "").strip(),
            first_name=claims.get("given_name", "").strip() or claims.get("name", "").strip(),
            last_name=claims.get("family_name", "").strip(),
        )
        user.set_unusable_password()
        user.save(update_fields=["password"])
        logger.info("OIDC auto-created local user '%s'.", user.username)
        create_audit_log(
            action=AuditLog.Action.USER_AUTOCREATED,
            module=MODULE,
            request=getattr(self, "request", None),
            user=user,
            object_type="User",
            object_id=user.pk,
            object_display=user.username,
            new_value={"email": user.email, "source": "oidc"},
        )
        self._sync_role_from_claims(user, claims)
        return user

    def update_user(self, user, claims):
        update_fields = []
        email = claims.get("email", "").strip()
        first_name = claims.get("given_name", "").strip() or claims.get("name", "").strip()
        last_name = claims.get("family_name", "").strip()
        if email and user.email != email:
            user.email = email
            update_fields.append("email")
        if first_name and user.first_name != first_name:
            user.first_name = first_name
            update_fields.append("first_name")
        if last_name and user.last_name != last_name:
            user.last_name = last_name
            update_fields.append("last_name")
        if update_fields:
            user.save(update_fields=update_fields)
        self._sync_role_from_claims(user, claims)
        return user

    def _sync_role_from_claims(self, user, claims):
        """Map Authentik melodu-* groups onto the local StaffProfile role.

        Fail-safe rules:
        - sync disabled (OIDC_SYNC_GROUPS=False) → never touch roles;
        - superusers are never modified;
        - groups claim entirely absent → keep the current (possibly manually
          assigned) role so a misconfigured claim cannot lock everyone out;
        - claim present → it is authoritative: highest melodu-* group wins,
          and no melodu-* group at all clears the role (no dashboard access).
        """
        if not getattr(settings, "OIDC_SYNC_GROUPS", True):
            return
        if user.is_superuser:
            return

        claim_name = getattr(settings, "OIDC_GROUPS_CLAIM", "groups")
        if claim_name not in claims:
            logger.warning(
                "OIDC claims for '%s' have no '%s' claim; keeping existing role.",
                user.username,
                claim_name,
            )
            return

        groups = claims.get(claim_name) or []
        if not isinstance(groups, (list, tuple, set)):
            groups = [groups]
        new_role = role_from_authentik_groups(groups)

        profile = StaffProfile.objects.filter(user=user).first()
        old_role = profile.role if profile else None
        if old_role == new_role:
            return

        from .services import set_role, sync_legacy_group

        set_role(user, new_role)
        sync_legacy_group(user, new_role)
        logger.info("OIDC group sync: '%s' role %s → %s.", user.username, old_role, new_role)
        create_audit_log(
            action=AuditLog.Action.GROUP_SYNC,
            module=MODULE,
            request=getattr(self, "request", None),
            user=user,
            object_type="User",
            object_id=user.pk,
            object_display=user.username,
            old_value={"role": old_role},
            new_value={"role": new_role, "authentik_groups": sorted(str(g) for g in groups)},
        )
