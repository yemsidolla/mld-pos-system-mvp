from django.contrib.auth.models import Group
from django.contrib.auth.signals import user_logged_in
from django.db.models.signals import post_migrate
from django.dispatch import receiver

from core.permissions import ADMIN_GROUP, CASHIER_GROUP

from .models import Role


@receiver(user_logged_in)
def apply_session_timeout(sender, request, user, **kwargs):
    """Honour the Owner-configured session lifetime for every login (Authz P5)."""
    if request is None:
        return
    from core.models import AuthSetting

    minutes = AuthSetting.load().session_timeout_minutes
    if minutes:
        request.session.set_expiry(minutes * 60)


@receiver(post_migrate)
def create_default_roles(sender, **kwargs):
    Group.objects.get_or_create(name=ADMIN_GROUP)
    Group.objects.get_or_create(name=CASHIER_GROUP)


@receiver(post_migrate)
def ensure_builtin_roles(sender, **kwargs):
    """Self-heal: create any missing built-in role (idempotent, never overwrites
    an existing/customized row). Belt-and-suspenders alongside the seed migration."""
    if sender is not None and getattr(sender, "label", None) != "accounts":
        return
    from core.capabilities import BUILTIN_ROLES

    for slug, name, rank, is_owner, capabilities in BUILTIN_ROLES:
        Role.objects.get_or_create(
            slug=slug,
            defaults={
                "name": name,
                "rank": rank,
                "is_owner": is_owner,
                "is_builtin": True,
                "capabilities": capabilities,
            },
        )
