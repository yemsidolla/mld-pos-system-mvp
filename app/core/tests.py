import os
from datetime import date
from decimal import Decimal
from tempfile import TemporaryDirectory
from unittest import mock

from django.conf import settings
from django.contrib.auth import SESSION_KEY, get_user_model
from django.contrib.auth.models import AnonymousUser, Group
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from accounts.models import StaffProfile
from audit.models import AuditLog
from batch_upload.models import BatchUploadJob, BatchUploadRow
from catalog.models import Product, Supplier
from core.models import StoreSetting
from core.permissions import (
    ADMIN_GROUP,
    CASHIER_GROUP,
    ROLE_CASHIER,
    ROLE_INVENTORY,
    ROLE_VIEWER,
)
from core.views import dashboard_server_error_view
from inventory.models import StockBatch
from inventory.services import receive_stock


class HealthUrlTests(SimpleTestCase):
    def test_health_url_resolves(self):
        self.assertEqual(reverse("health-check"), "/health/")


class HealthCheckTests(TestCase):
    def test_health_reports_migrations_ok_when_database_is_current(self):
        response = self.client.get(reverse("health-check"))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["database"], "ok")
        self.assertEqual(payload["migrations"], "ok")

    @mock.patch("core.views.MigrationExecutor")
    def test_health_reports_unapplied_migrations(self, executor_class):
        # Mock(name=...) sets the mock's repr name, so assign .name explicitly.
        migration = mock.Mock(app_label="sessions")
        migration.name = "0001_initial"
        executor = executor_class.return_value
        executor.loader.graph.leaf_nodes.return_value = [("sessions", "0001_initial")]
        executor.migration_plan.return_value = [(migration, False)]

        response = self.client.get(reverse("health-check"))

        self.assertEqual(response.status_code, 503)
        payload = response.json()
        self.assertEqual(payload["status"], "degraded")
        self.assertEqual(payload["migrations"], "unapplied")
        self.assertEqual(payload["unapplied_migration_count"], 1)
        self.assertEqual(payload["unapplied_migrations"], ["sessions.0001_initial"])


class DashboardShellTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_user(
            username="admin",
            password="Admin123",
            is_staff=True,
            is_superuser=True,
        )
        self.cashier = get_user_model().objects.create_user(username="cashier", password="Admin123")
        cashier_group, _created = Group.objects.get_or_create(name=CASHIER_GROUP)
        self.cashier.groups.add(cashier_group)

    def test_dashboard_url_resolves(self):
        self.assertEqual(reverse("dashboard-home"), "/dashboard/")
        self.assertEqual(reverse("dashboard-login"), "/dashboard/login/")
        self.assertEqual(reverse("dashboard-logout"), "/dashboard/logout/")

    def test_language_settings_include_english_and_khmer(self):
        self.assertIn(("en", "English"), settings.LANGUAGES)
        self.assertIn(("km", "ភាសាខ្មែរ"), settings.LANGUAGES)

    def test_admin_dashboard_shows_admin_navigation(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse("dashboard-home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Melodu Dashboard")
        self.assertContains(response, "Products")
        self.assertContains(response, "Costs")
        self.assertContains(response, "Promotions")
        self.assertContains(response, "Batch Upload")
        self.assertContains(response, "Django Admin")

    def test_cashier_dashboard_hides_admin_navigation(self):
        self.client.force_login(self.cashier)

        response = self.client.get(reverse("dashboard-home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "POS")
        self.assertNotContains(response, "Costs")
        self.assertNotContains(response, "Promotions")
        self.assertNotContains(response, "Batch Upload")
        self.assertNotContains(response, "Django Admin")


class RoleAwareHomeTests(TestCase):
    """V5 Phase 1: the home page must match each role's real capabilities.

    Inventory staff and Viewers cannot access POS, so the home page must never
    offer them POS shortcuts (which would dead-end at a 403).
    """

    def _user(self, username, role):
        user = get_user_model().objects.create_user(username=username, password="Admin123")
        StaffProfile.objects.create(user=user, role=role)
        return user

    def test_inventory_home_shows_stock_tools_and_no_pos(self):
        self.client.force_login(self._user("inv", ROLE_INVENTORY))

        response = self.client.get(reverse("dashboard-home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Receive Stock")
        self.assertContains(response, "Stock Overview")
        self.assertNotContains(response, "Open POS")
        self.assertNotContains(response, "POS Sale")

    def test_viewer_home_shows_reports_and_no_pos(self):
        self.client.force_login(self._user("aud", ROLE_VIEWER))

        response = self.client.get(reverse("dashboard-home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Reports")
        self.assertContains(response, "Sales History")
        self.assertNotContains(response, "Open POS")
        self.assertNotContains(response, "POS Sale")
        # Viewer is read-only: no receiving shortcut.
        self.assertNotContains(response, "Receive Stock")

    def test_cashier_home_shows_pos(self):
        self.client.force_login(self._user("csh", ROLE_CASHIER))

        response = self.client.get(reverse("dashboard-home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Open POS")
        self.assertContains(response, "POS Sale")

    def test_mobile_nav_is_role_weighted_and_capped(self):
        self.client.force_login(self._user("cmob", ROLE_CASHIER))
        cashier_nav = self.client.get(reverse("dashboard-home")).context["dashboard_mobile_nav_items"]
        cashier_urls = [item["url_name"] for item in cashier_nav]
        # Cashier only gets the destinations they can actually use.
        self.assertEqual(cashier_urls, ["dashboard-home", "pos-sale"])

        owner = get_user_model().objects.create_user(
            username="omob", password="Admin123", is_superuser=True, is_staff=True
        )
        self.client.force_login(owner)
        owner_nav = self.client.get(reverse("dashboard-home")).context["dashboard_mobile_nav_items"]
        owner_urls = [item["url_name"] for item in owner_nav]
        # Capped at 5, prioritized by usefulness (Stock Overview over Categories).
        self.assertEqual(len(owner_urls), 5)
        self.assertIn("inventory-summary", owner_urls)
        self.assertNotIn("category-list", owner_urls)


class DashboardAuthTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_user(
            username="auth-admin",
            password="Admin123",
            is_staff=True,
            is_superuser=True,
        )
        self.cashier = get_user_model().objects.create_user(username="auth-cashier", password="Admin123")
        self.cashier.groups.add(Group.objects.get(name=CASHIER_GROUP))
        self.unassigned = get_user_model().objects.create_user(username="unassigned", password="Admin123")

    def test_unauthenticated_dashboard_redirects_to_dashboard_login(self):
        response = self.client.get(reverse("dashboard-home"))

        self.assertRedirects(response, f"{reverse('dashboard-login')}?next={reverse('dashboard-home')}")

    def test_login_success_redirects_to_dashboard(self):
        response = self.client.post(
            reverse("dashboard-login"),
            {"username": "auth-admin", "password": "Admin123"},
        )

        self.assertRedirects(response, reverse("dashboard-home"))
        self.assertIn(SESSION_KEY, self.client.session)

    def test_login_uses_safe_next_url(self):
        response = self.client.post(
            reverse("dashboard-login"),
            {"username": "auth-cashier", "password": "Admin123", "next": reverse("pos-sale")},
        )

        self.assertRedirects(response, reverse("pos-sale"))

    def test_login_rejects_unsafe_next_url(self):
        response = self.client.post(
            reverse("dashboard-login"),
            {"username": "auth-admin", "password": "Admin123", "next": "https://example.com/steal"},
        )

        self.assertRedirects(response, reverse("dashboard-home"))

    def test_authenticated_user_opening_login_redirects_to_dashboard(self):
        self.client.force_login(self.cashier)

        response = self.client.get(reverse("dashboard-login"))

        self.assertRedirects(response, reverse("dashboard-home"))

    def test_logout_requires_post_and_returns_to_login(self):
        self.client.force_login(self.cashier)

        get_response = self.client.get(reverse("dashboard-logout"))
        post_response = self.client.post(reverse("dashboard-logout"), follow=True)

        self.assertEqual(get_response.status_code, 405)
        self.assertRedirects(post_response, reverse("dashboard-login"))
        self.assertContains(post_response, "You have logged out successfully.")
        self.assertNotIn(SESSION_KEY, self.client.session)

    def test_inactive_user_cannot_log_in(self):
        inactive = get_user_model().objects.create_user(username="inactive", password="Admin123", is_active=False)
        inactive.groups.add(Group.objects.get(name=ADMIN_GROUP))

        response = self.client.post(
            reverse("dashboard-login"),
            {"username": "inactive", "password": "Admin123"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Check your username and password")
        self.assertNotIn(SESSION_KEY, self.client.session)

    def test_unassigned_user_receives_friendly_access_denied(self):
        self.client.force_login(self.unassigned)

        response = self.client.get(reverse("dashboard-home"))

        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "No role assigned", status_code=403)

    def test_force_logged_inactive_user_is_treated_as_anonymous(self):
        inactive = get_user_model().objects.create_user(username="forced-inactive", password="Admin123", is_active=False)
        inactive.groups.add(Group.objects.get(name=ADMIN_GROUP))
        self.client.force_login(inactive)

        response = self.client.get(reverse("dashboard-home"))

        self.assertRedirects(response, f"{reverse('dashboard-login')}?next={reverse('dashboard-home')}")


class DashboardErrorPageTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_user(
            username="error-admin",
            password="Admin123",
            is_staff=True,
            is_superuser=True,
        )
        self.cashier = get_user_model().objects.create_user(username="error-cashier", password="Admin123")
        self.cashier.groups.add(Group.objects.get(name=CASHIER_GROUP))

    def test_cashier_denial_renders_friendly_403(self):
        self.client.force_login(self.cashier)

        response = self.client.get(reverse("product-list"))

        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "Access denied", status_code=403)
        self.assertContains(response, "Back to POS", status_code=403)

    @override_settings(DEBUG=False, ALLOWED_HOSTS=["testserver"])
    def test_missing_dashboard_object_renders_friendly_404(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse("product-edit", kwargs={"product_id": 999999}))

        self.assertEqual(response.status_code, 404)
        self.assertContains(response, "Page or item not found", status_code=404)

    def test_server_error_handler_renders_friendly_500(self):
        request = RequestFactory().get("/dashboard/error/")
        request.user = AnonymousUser()

        response = dashboard_server_error_view(request)

        self.assertEqual(response.status_code, 500)
        self.assertIn(b"Unexpected error", response.content)


class ScanResolveTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_user(
            username="scanner-admin",
            password="Admin123",
            is_staff=True,
            is_superuser=True,
        )
        self.supplier = Supplier.objects.create(name="Pet Wholesale")
        self.product = Product.objects.create(
            product_code="P001",
            original_barcode="8851234567890",
            name="Cat Food",
            default_cost_price=Decimal("1.50"),
            default_selling_price=Decimal("2.50"),
        )

    def create_batch(self):
        with TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            stock_batch, _movement = receive_stock(
                product=self.product,
                supplier=self.supplier,
                quantity=10,
                expiry_date=date(2027, 6, 1),
                actual_unit_cost=Decimal("1.50"),
                selling_price=Decimal("2.50"),
                received_by=self.admin,
            )
        return StockBatch.objects.get(pk=stock_batch.pk)

    def test_scan_resolver_resolves_original_barcode(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse("scan-resolve"), {"value": "8851234567890", "context": "pos"})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["match_type"], "original_barcode")
        self.assertEqual(payload["product"]["product_code"], "P001")

    def test_scan_resolver_resolves_custom_code_to_batch(self):
        stock_batch = self.create_batch()
        self.client.force_login(self.admin)

        response = self.client.get(reverse("scan-resolve"), {"value": stock_batch.custom_code, "context": "pos"})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["match_type"], "custom_code")
        self.assertEqual(payload["stock_batch"]["batch_no"], stock_batch.batch_no)

    def test_scan_resolver_rejects_unknown_and_malformed_codes(self):
        self.client.force_login(self.admin)

        unknown = self.client.get(reverse("scan-resolve"), {"value": "UNKNOWN"})
        malformed = self.client.get(reverse("scan-resolve"), {"value": "885-M-BAD-B260001"})

        self.assertEqual(unknown.status_code, 404)
        self.assertEqual(malformed.status_code, 400)

    def test_anonymous_scan_resolver_redirects_to_login(self):
        response = self.client.get(reverse("scan-resolve"), {"value": "8851234567890"})

        self.assertEqual(response.status_code, 302)


class ScannerPlacementTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_user(
            username="ui-admin",
            password="Admin123",
            is_staff=True,
            is_superuser=True,
        )
        self.cashier = get_user_model().objects.create_user(username="ui-cashier", password="Admin123")
        cashier_group, _created = Group.objects.get_or_create(name=CASHIER_GROUP)
        self.cashier.groups.add(cashier_group)

    def test_scan_controls_appear_on_pos_stock_inventory_and_labels(self):
        self.client.force_login(self.cashier)
        pos_response = self.client.get(reverse("pos-sale"))
        self.assertContains(pos_response, 'data-scan-target="#id_scan_value"')

        self.client.force_login(self.admin)
        stock_response = self.client.get(reverse("stock-in"))
        labels_response = self.client.get(reverse("barcode-print"))
        inventory_response = self.client.get(reverse("inventory-summary"))

        self.assertContains(stock_response, 'data-scan-select-target="#id_product"')
        self.assertContains(labels_response, 'data-scan-select-target="#id_stock_batch"')
        self.assertContains(inventory_response, 'data-scan-target="#inventory-search"')

    def test_scan_controls_appear_on_batch_upload_preview_code_fields(self):
        self.client.force_login(self.admin)
        job = BatchUploadJob.objects.create(
            target=BatchUploadJob.Target.PRODUCTS,
            original_filename="products.csv",
            uploaded_by=self.admin,
        )
        BatchUploadRow.objects.create(
            job=job,
            row_number=2,
            raw_data={},
            normalized_data={
                "product_code": "P001",
                "original_barcode": "8851234567890",
                "name": "Cat Food",
            },
        )

        response = self.client.get(reverse("batch-upload-detail", kwargs={"job_id": job.id}))

        self.assertContains(response, 'data-scan-context="batch_upload"')
        self.assertContains(response, 'row-')


class StoreSettingTests(TestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user(
            username="settings-owner", password="Admin123", is_staff=True, is_superuser=True
        )
        self.cashier = get_user_model().objects.create_user(username="settings-cashier", password="Admin123")
        self.cashier.groups.add(Group.objects.get_or_create(name=CASHIER_GROUP)[0])

    def test_load_returns_single_default_row(self):
        first = StoreSetting.load()
        second = StoreSetting.load()
        self.assertEqual(first.pk, 1)
        self.assertEqual(second.pk, 1)
        self.assertEqual(StoreSetting.objects.count(), 1)
        self.assertEqual(first.receipt_paper_width_mm, 80)

    def test_save_always_uses_single_row(self):
        setting = StoreSetting.load()
        setting.store_name = "Changed"
        setting.save()
        again = StoreSetting.load()
        again.store_name = "Second"
        again.save()
        self.assertEqual(StoreSetting.objects.count(), 1)
        self.assertEqual(StoreSetting.load().store_name, "Second")

    def test_owner_can_open_settings_but_cashier_cannot(self):
        self.client.force_login(self.owner)
        self.assertEqual(self.client.get(reverse("store-settings")).status_code, 200)

        self.client.force_login(self.cashier)
        self.assertEqual(self.client.get(reverse("store-settings")).status_code, 403)

    def test_update_settings_persists_and_audits(self):
        self.client.force_login(self.owner)
        response = self.client.post(
            reverse("store-settings"),
            {
                "store_name": "Khlove Pet",
                "address": "Phnom Penh",
                "phone": "012000111",
                "receipt_header": "",
                "receipt_footer": "Thank you!",
                "receipt_paper_width_mm": "80",
                "receipt_font_size_px": "12",
                "currency_symbol": "$",
            },
        )
        self.assertRedirects(response, reverse("store-settings"))
        self.assertEqual(StoreSetting.load().store_name, "Khlove Pet")
        self.assertTrue(
            AuditLog.objects.filter(action=AuditLog.Action.SETTING_CHANGE, module="core").exists()
        )

    def test_invalid_paper_width_is_rejected(self):
        self.client.force_login(self.owner)
        response = self.client.post(
            reverse("store-settings"),
            {
                "store_name": "Store",
                "receipt_footer": "Thanks",
                "receipt_paper_width_mm": "5",
                "receipt_font_size_px": "12",
                "currency_symbol": "$",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "between 40mm and 120mm")


class ResetBusinessDataCommandTests(TestCase):
    def setUp(self):
        from pos.models import Sale, SaleItem

        self.owner = get_user_model().objects.create_user(
            username="reset-owner", password="Admin123", is_staff=True, is_superuser=True
        )
        self.supplier = Supplier.objects.create(name="Pet Wholesale")
        self.product = Product.objects.create(
            product_code="P001",
            original_barcode="8851234567890",
            name="Cat Food",
            default_cost_price=Decimal("1.50"),
            default_selling_price=Decimal("2.50"),
        )
        with TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            self.batch, _movement = receive_stock(
                product=self.product,
                supplier=self.supplier,
                quantity=10,
                expiry_date=date(2027, 6, 1),
                actual_unit_cost=Decimal("1.50"),
                selling_price=Decimal("2.50"),
                received_by=self.owner,
            )
        self.sale = Sale.objects.create(
            sale_no="S2606090001",
            cashier=self.owner,
            total_amount=Decimal("2.50"),
            final_amount=Decimal("2.50"),
        )
        SaleItem.objects.create(
            sale=self.sale,
            product=self.product,
            stock_batch=self.batch,
            quantity=1,
            unit_price=Decimal("2.50"),
            subtotal=Decimal("2.50"),
        )

    def test_dry_run_deletes_nothing(self):
        from pos.models import Sale

        call_command("reset_business_data", "--scope", "sales")
        self.assertEqual(Sale.objects.count(), 1)
        self.assertEqual(StockBatch.objects.count(), 1)

    def test_execute_requires_environment_flag(self):
        with self.assertRaisesMessage(CommandError, "ALLOW_DATA_RESET"):
            call_command(
                "reset_business_data",
                "--scope",
                "sales",
                "--confirm",
                "--phrase",
                "RESET sales",
                "--backup-confirmed",
            )

    def test_execute_requires_exact_phrase(self):
        with mock.patch.dict(os.environ, {"ALLOW_DATA_RESET": "1"}):
            with self.assertRaisesMessage(CommandError, "phrase"):
                call_command(
                    "reset_business_data",
                    "--scope",
                    "sales",
                    "--confirm",
                    "--phrase",
                    "WRONG",
                    "--backup-confirmed",
                )

    def test_execute_requires_backup_confirmation(self):
        with mock.patch.dict(os.environ, {"ALLOW_DATA_RESET": "1"}):
            with self.assertRaisesMessage(CommandError, "backup"):
                call_command(
                    "reset_business_data",
                    "--scope",
                    "sales",
                    "--confirm",
                    "--phrase",
                    "RESET sales",
                )

    def test_sales_scope_clears_sales_but_keeps_catalog_and_audits(self):
        from pos.models import Sale, SaleItem

        with mock.patch.dict(os.environ, {"ALLOW_DATA_RESET": "1"}):
            call_command(
                "reset_business_data",
                "--scope",
                "sales",
                "--confirm",
                "--phrase",
                "RESET sales",
                "--backup-confirmed",
            )

        self.assertEqual(Sale.objects.count(), 0)
        self.assertEqual(SaleItem.objects.count(), 0)
        # Catalog and stock master data survive a sales-only reset.
        self.assertEqual(Product.objects.count(), 1)
        self.assertEqual(StockBatch.objects.count(), 1)
        # Users are never deleted; before/after audit entries are recorded.
        self.assertTrue(get_user_model().objects.filter(username="reset-owner").exists())
        self.assertEqual(
            AuditLog.objects.filter(action=AuditLog.Action.DATA_RESET).count(), 2
        )

    def test_all_scope_clears_catalog_but_preserves_owner_and_audit(self):
        from pos.models import Sale

        with mock.patch.dict(os.environ, {"ALLOW_DATA_RESET": "1"}):
            call_command(
                "reset_business_data",
                "--scope",
                "all",
                "--confirm",
                "--phrase",
                "RESET all",
                "--backup-confirmed",
            )

        self.assertEqual(Sale.objects.count(), 0)
        self.assertEqual(StockBatch.objects.count(), 0)
        self.assertEqual(Product.objects.count(), 0)
        self.assertEqual(Supplier.objects.count(), 0)
        self.assertTrue(get_user_model().objects.filter(username="reset-owner").exists())
        self.assertTrue(AuditLog.objects.filter(action=AuditLog.Action.DATA_RESET).exists())
