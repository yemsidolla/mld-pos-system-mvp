from pathlib import Path
from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from .views import read_latest_log_lines, redact_log_line


class SystemLogTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_user(
            username="admin",
            password="Admin123",
            is_staff=True,
            is_superuser=True,
        )
        self.cashier = get_user_model().objects.create_user(
            username="cashier",
            password="Admin123",
            is_staff=True,
        )

    def test_read_latest_log_lines_returns_newest_first(self):
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "app.log"
            path.write_text("old\nnew\n")

            self.assertEqual(read_latest_log_lines(path), ["new", "old"])

    def test_log_redaction_removes_secret_key(self):
        with override_settings(SECRET_KEY="very-secret-key"):
            self.assertEqual(redact_log_line("value=very-secret-key"), "value=[REDACTED]")

    def test_admin_can_view_live_logs(self):
        with TemporaryDirectory() as tmpdir, override_settings(LOG_DIR=Path(tmpdir)):
            Path(tmpdir, "app.log").write_text("INFO app started\n")
            Path(tmpdir, "error.log").write_text("ERROR sample\n")
            self.client.force_login(self.admin)

            response = self.client.get(reverse("live-logs"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "INFO app started")
        self.assertContains(response, "ERROR sample")

    def test_admin_can_view_system_health(self):
        with TemporaryDirectory() as tmpdir, override_settings(LOG_DIR=Path(tmpdir)):
            Path(tmpdir, "error.log").write_text("ERROR latest\n")
            self.client.force_login(self.admin)

            response = self.client.get(reverse("system-health"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Database Status")
        self.assertContains(response, "Log Writable Status")
        self.assertContains(response, "ERROR latest")

    def test_cashier_cannot_view_logs_or_health(self):
        self.client.force_login(self.cashier)

        logs_response = self.client.get(reverse("live-logs"))
        health_response = self.client.get(reverse("system-health"))

        self.assertEqual(logs_response.status_code, 302)
        self.assertEqual(health_response.status_code, 302)
