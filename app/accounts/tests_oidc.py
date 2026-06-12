"""V6 tests: Authentik OIDC login, group→role sync, and access safety.

The OIDC network calls are mocked at the backend boundary (get_token /
verify_token / get_userinfo) so the full Django callback flow — session state,
user creation, login, redirects — runs for real.
"""
import time
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import include, path, reverse

from accounts.models import StaffProfile
from accounts.oidc import MeloduOIDCBackend, role_from_authentik_groups
from audit.models import AuditLog
from core.permissions import (
    ADMIN_GROUP,
    CASHIER_GROUP,
    ROLE_CASHIER,
    ROLE_INVENTORY,
    ROLE_MANAGER,
    ROLE_OWNER,
    ROLE_VIEWER,
    get_user_role,
)
from melodu_pos.urls import urlpatterns as base_urlpatterns

User = get_user_model()

# Test URLConf with the OIDC routes always mounted, regardless of AUTH_MODE in
# the environment the suite happens to run under.
urlpatterns = list(base_urlpatterns)
if not any(getattr(p, "app_name", "") == "mozilla_django_oidc" for p in urlpatterns):
    urlpatterns += [path("oidc/", include("mozilla_django_oidc.urls"))]

OIDC_TEST_SETTINGS = {
    "ROOT_URLCONF": "accounts.tests_oidc",
    "OIDC_ENABLED": True,
    "LOCAL_LOGIN_ENABLED": True,
    "OIDC_RP_CLIENT_ID": "melodu-pos",
    "OIDC_RP_CLIENT_SECRET": "test-secret",
    "OIDC_OP_AUTHORIZATION_ENDPOINT": "https://auth.example.com/authorize/",
    "OIDC_OP_TOKEN_ENDPOINT": "https://auth.example.com/token/",
    "OIDC_OP_USER_ENDPOINT": "https://auth.example.com/userinfo/",
    "OIDC_OP_JWKS_ENDPOINT": "https://auth.example.com/jwks/",
    "AUTHENTICATION_BACKENDS": [
        "django.contrib.auth.backends.ModelBackend",
        "accounts.oidc.MeloduOIDCBackend",
    ],
}


def make_claims(**overrides):
    claims = {
        "sub": "authentik-sub-1",
        "preferred_username": "sokha",
        "email": "sokha@khlovepet.com",
        "given_name": "Sokha",
        "family_name": "Chan",
        "groups": ["melodu-cashier"],
    }
    claims.update(overrides)
    return claims


class GroupRoleMappingTests(TestCase):
    def test_each_authentik_group_maps_to_expected_role(self):
        cases = {
            "melodu-admin": ROLE_OWNER,
            "melodu-manager": ROLE_MANAGER,
            "melodu-inventory": ROLE_INVENTORY,
            "melodu-cashier": ROLE_CASHIER,
            "melodu-report-viewer": ROLE_VIEWER,
        }
        for group, role in cases.items():
            self.assertEqual(role_from_authentik_groups([group]), role)

    def test_highest_role_wins_and_unknown_groups_ignored(self):
        self.assertEqual(
            role_from_authentik_groups(["random", "melodu-cashier", "melodu-manager"]),
            ROLE_MANAGER,
        )
        self.assertIsNone(role_from_authentik_groups(["random", "staff"]))
        self.assertIsNone(role_from_authentik_groups([]))


@override_settings(**OIDC_TEST_SETTINGS)
class OIDCBackendSyncTests(TestCase):
    def setUp(self):
        self.backend = MeloduOIDCBackend()

    def test_create_user_sets_identity_role_and_audit(self):
        user = self.backend.create_user(make_claims())
        self.assertEqual(user.username, "sokha")
        self.assertEqual(user.email, "sokha@khlovepet.com")
        self.assertFalse(user.has_usable_password())
        self.assertEqual(get_user_role(user), ROLE_CASHIER)
        self.assertTrue(user.groups.filter(name=CASHIER_GROUP).exists())
        self.assertTrue(
            AuditLog.objects.filter(action=AuditLog.Action.USER_AUTOCREATED, object_id=str(user.pk)).exists()
        )
        self.assertTrue(
            AuditLog.objects.filter(action=AuditLog.Action.GROUP_SYNC, object_id=str(user.pk)).exists()
        )

    def test_update_user_syncs_identity_and_role_change(self):
        user = self.backend.create_user(make_claims())
        self.backend.update_user(
            user,
            make_claims(email="new@khlovepet.com", groups=["melodu-manager"]),
        )
        user.refresh_from_db()
        self.assertEqual(user.email, "new@khlovepet.com")
        self.assertEqual(get_user_role(user), ROLE_MANAGER)
        self.assertTrue(user.groups.filter(name=ADMIN_GROUP).exists())
        self.assertFalse(user.groups.filter(name=CASHIER_GROUP).exists())

    def test_removed_group_clears_role_and_access(self):
        user = self.backend.create_user(make_claims())
        self.backend.update_user(user, make_claims(groups=[]))
        user = User.objects.get(pk=user.pk)  # drop cached staff_profile relation
        self.assertIsNone(get_user_role(user))
        self.assertFalse(StaffProfile.objects.filter(user=user).exists())
        self.assertFalse(user.groups.filter(name=CASHIER_GROUP).exists())

    def test_missing_groups_claim_keeps_existing_role(self):
        user = self.backend.create_user(make_claims())
        claims = make_claims()
        del claims["groups"]
        self.backend.update_user(user, claims)
        self.assertEqual(get_user_role(user), ROLE_CASHIER)

    @override_settings(OIDC_SYNC_GROUPS=False)
    def test_sync_disabled_never_touches_roles(self):
        user = User.objects.create_user("manual", password="x")
        StaffProfile.objects.create(user=user, role=ROLE_MANAGER)
        self.backend.update_user(user, make_claims(preferred_username="manual", groups=[]))
        self.assertEqual(get_user_role(user), ROLE_MANAGER)

    def test_superuser_never_modified_by_sync(self):
        boss = User.objects.create_superuser("boss", "boss@x.com", "x")
        self.backend.update_user(boss, make_claims(preferred_username="boss", groups=[]))
        boss.refresh_from_db()
        self.assertTrue(boss.is_superuser)
        self.assertEqual(get_user_role(boss), ROLE_OWNER)

    def test_existing_user_matched_by_username_then_email(self):
        existing = User.objects.create_user("sokha", "old@khlovepet.com", "x")
        users = self.backend.filter_users_by_claims(make_claims())
        self.assertEqual(list(users), [existing])

        by_email = User.objects.create_user("other", "mail-match@khlovepet.com", "x")
        users = self.backend.filter_users_by_claims(
            make_claims(preferred_username="unknown", email="mail-match@khlovepet.com")
        )
        self.assertEqual(list(users), [by_email])

    def test_inactive_user_denied_with_audit(self):
        user = User.objects.create_user("gone", password="x", is_active=False)
        with mock.patch(
            "mozilla_django_oidc.auth.OIDCAuthenticationBackend.authenticate",
            return_value=user,
        ):
            result = MeloduOIDCBackend().authenticate(request=None)
        self.assertIsNone(result)
        self.assertTrue(
            AuditLog.objects.filter(action=AuditLog.Action.LOGIN_FAILED, object_display="gone").exists()
        )


@override_settings(**OIDC_TEST_SETTINGS)
class OIDCCallbackFlowTests(TestCase):
    """Full mocked login: callback → user auto-created → session established."""

    def _login_via_callback(self, claims):
        session = self.client.session
        session["oidc_states"] = {"state123": {"nonce": None, "added_on": time.time()}}
        session.save()
        with mock.patch.object(MeloduOIDCBackend, "get_token", return_value={"id_token": "t", "access_token": "a"}), \
                mock.patch.object(MeloduOIDCBackend, "verify_token", return_value={"sub": claims["sub"]}), \
                mock.patch.object(MeloduOIDCBackend, "get_userinfo", return_value=claims):
            return self.client.get(
                reverse("oidc_authentication_callback"), {"code": "code123", "state": "state123"}
            )

    def test_mocked_oidc_login_creates_user_and_logs_in(self):
        response = self._login_via_callback(make_claims())
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/dashboard/")
        user = User.objects.get(username="sokha")
        self.assertEqual(get_user_role(user), ROLE_CASHIER)
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)
        self.assertTrue(
            AuditLog.objects.filter(action=AuditLog.Action.LOGIN_SUCCESS, object_display="sokha").exists()
        )

    def test_user_without_melodu_group_gets_no_access_page(self):
        self._login_via_callback(make_claims(groups=[]))
        response = self.client.get(reverse("dashboard-home"))
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "No role assigned", status_code=403)


@override_settings(**OIDC_TEST_SETTINGS)
class LoginPageOIDCModeTests(TestCase):
    def test_login_page_shows_sso_button_and_hides_local_form(self):
        response = self.client.get(reverse("dashboard-login"))
        self.assertContains(response, "Continue with Melodu Staff Login")
        self.assertNotContains(response, 'name="password"')

    def test_emergency_local_form_available_with_flag(self):
        response = self.client.get(reverse("dashboard-login"), {"local": "1"})
        self.assertContains(response, 'name="password"')

    @override_settings(LOCAL_LOGIN_ENABLED=False)
    def test_local_form_fully_disabled_when_configured(self):
        response = self.client.get(reverse("dashboard-login"), {"local": "1"})
        self.assertNotContains(response, 'name="password"')

    def test_emergency_local_superuser_can_still_login(self):
        User.objects.create_superuser("emergency", "e@x.com", "rescue-pass-123")
        response = self.client.post(
            reverse("dashboard-login") + "?local=1",
            {"username": "emergency", "password": "rescue-pass-123", "local_login": "1", "next": ""},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/dashboard/")

    def test_oidc_error_shows_friendly_message(self):
        response = self.client.get(reverse("dashboard-login"), {"oidc_error": "1"})
        self.assertContains(response, "could not be completed")


class LocalModeUnchangedTests(TestCase):
    """AUTH_MODE=local (rollback mode) keeps the classic login behavior."""

    def test_login_page_shows_form_without_sso(self):
        response = self.client.get(reverse("dashboard-login"))
        self.assertContains(response, 'name="password"')
        self.assertNotContains(response, "Continue with Melodu Staff Login")

    def test_logout_writes_audit_log(self):
        user = User.objects.create_user("worker", password="x")
        StaffProfile.objects.create(user=user, role=ROLE_CASHIER)
        self.client.force_login(user)
        self.client.post(reverse("dashboard-logout"))
        self.assertTrue(
            AuditLog.objects.filter(action=AuditLog.Action.LOGOUT, object_display="worker").exists()
        )


class PermissionDeniedAuditTests(TestCase):
    def test_cashier_blocked_from_admin_pages_with_audit_trail(self):
        user = User.objects.create_user("till", password="x")
        StaffProfile.objects.create(user=user, role=ROLE_CASHIER)
        self.client.force_login(user)
        response = self.client.get(reverse("user-list"))
        self.assertEqual(response.status_code, 403)
        self.assertTrue(
            AuditLog.objects.filter(
                action=AuditLog.Action.PERMISSION_DENIED,
                user=user,
            ).exists()
        )

    def test_inventory_user_can_open_inventory(self):
        user = User.objects.create_user("stock", password="x")
        StaffProfile.objects.create(user=user, role=ROLE_INVENTORY)
        self.client.force_login(user)
        response = self.client.get(reverse("inventory-summary"))
        self.assertEqual(response.status_code, 200)
