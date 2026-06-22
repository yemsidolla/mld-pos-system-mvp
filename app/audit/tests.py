from django.contrib import admin
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from accounts.models import StaffProfile
from core.permissions import ROLE_CASHIER, ROLE_MANAGER, ROLE_VIEWER

from .admin import AuditLogAdmin
from .models import AuditLog
from .services import create_audit_log, get_client_ip


class AuditHelperTests(TestCase):
    def test_create_audit_log_captures_user_ip_and_user_agent(self):
        user = get_user_model().objects.create_user(username="tester", password="Admin123")
        request = self.client.request().wsgi_request
        request.user = user
        request.META["REMOTE_ADDR"] = "127.0.0.1"
        request.META["HTTP_USER_AGENT"] = "AuditTestBrowser"

        log = create_audit_log(
            action=AuditLog.Action.CREATE,
            module="catalog",
            request=request,
            object_type="Product",
            object_id=12,
            object_display="Cat Food",
            new_value={"name": "Cat Food"},
        )

        self.assertEqual(log.user, user)
        self.assertEqual(log.ip_address, "127.0.0.1")
        self.assertEqual(log.user_agent, "AuditTestBrowser")
        self.assertEqual(log.object_id, "12")

    def test_get_client_ip_prefers_forwarded_for(self):
        request = self.client.request().wsgi_request
        request.META["REMOTE_ADDR"] = "10.0.0.2"
        request.META["HTTP_X_FORWARDED_FOR"] = "203.0.113.10, 10.0.0.2"

        self.assertEqual(get_client_ip(request), "203.0.113.10")


class AuditAdminTests(TestCase):
    def test_audit_admin_is_registered_and_read_only(self):
        audit_admin = admin.site._registry[AuditLog]
        request = self.client.request().wsgi_request

        self.assertIsInstance(audit_admin, AuditLogAdmin)
        self.assertFalse(audit_admin.has_add_permission(request))
        self.assertFalse(audit_admin.has_delete_permission(request))
        self.assertIn("created_at", audit_admin.get_readonly_fields(request))


class AuditLoginSignalTests(TestCase):
    def test_login_success_creates_audit_log(self):
        get_user_model().objects.create_user(username="cashier", password="Admin123")

        logged_in = self.client.login(username="cashier", password="Admin123")

        self.assertTrue(logged_in)
        self.assertTrue(AuditLog.objects.filter(action=AuditLog.Action.LOGIN_SUCCESS).exists())

    def test_login_failed_creates_audit_log_without_password(self):
        logged_in = self.client.login(username="missing", password="wrong-password")

        self.assertFalse(logged_in)
        log = AuditLog.objects.get(action=AuditLog.Action.LOGIN_FAILED)
        self.assertEqual(log.object_display, "missing")
        self.assertNotIn("wrong-password", str(log.old_value))
        self.assertNotIn("wrong-password", str(log.new_value))


class AuditLogDashboardTests(TestCase):
    """V5 Phase 2: read-only audit dashboard for Owner/Manager."""

    def _user(self, username, role):
        user = get_user_model().objects.create_user(username=username, password="Admin123")
        StaffProfile.objects.create(user=user, role=role)
        return user

    def setUp(self):
        self.manager = self._user("mgr", ROLE_MANAGER)
        AuditLog.objects.create(
            action=AuditLog.Action.CREATE,
            module="catalog",
            object_type="Product",
            object_id="P001",
            object_display="Widget",
        )
        AuditLog.objects.create(
            action=AuditLog.Action.SETTING_CHANGE,
            module="core",
            object_type="StoreSetting",
            object_id="1",
            object_display="Store",
        )

    def test_manager_can_view_audit_logs(self):
        self.client.force_login(self.manager)

        response = self.client.get(reverse("audit-log-list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Widget")
        self.assertContains(response, "Store")
        self.assertContains(response, "Read-only")
        self.assertContains(response, "Newest first")
        self.assertContains(response, "Risk Events")
        self.assertContains(response, "Object Type")
        self.assertContains(response, "Review")

    def test_cashier_and_viewer_cannot_view_audit_logs(self):
        for username, role in (("csh", ROLE_CASHIER), ("aud", ROLE_VIEWER)):
            self.client.force_login(self._user(username, role))
            response = self.client.get(reverse("audit-log-list"))
            self.assertEqual(response.status_code, 403)

    def test_action_filter_narrows_results(self):
        self.client.force_login(self.manager)

        response = self.client.get(
            reverse("audit-log-list"), {"action": AuditLog.Action.SETTING_CHANGE}
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Store")
        self.assertNotContains(response, "Widget")

    def test_search_and_object_type_filters_narrow_results(self):
        self.client.force_login(self.manager)

        response = self.client.get(reverse("audit-log-list"), {"q": "P001", "object_type": "Product"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Widget")
        self.assertNotContains(response, "StoreSetting #1")
        self.assertEqual(response.context["summary"]["total_count"], 1)

    def test_audit_dashboard_does_not_write_audit_records(self):
        # The page is strictly read-only: a POST must not create/modify entries.
        self.client.force_login(self.manager)
        count_before = AuditLog.objects.count()

        response = self.client.post(reverse("audit-log-list"), {})

        self.assertEqual(AuditLog.objects.count(), count_before)
        self.assertIn(response.status_code, (200, 405))
