import os
from datetime import date
from decimal import Decimal
from tempfile import TemporaryDirectory
from unittest import mock

from django.conf import settings
from django.contrib.auth import SESSION_KEY, get_user_model
from django.contrib.auth.models import AnonymousUser, Group
from django.core.exceptions import ImproperlyConfigured
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from django.utils.translation import gettext, override

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
from inventory.forms import StockInForm
from labels.forms import LabelPrintForm as TemplateLabelPrintForm
from pos.forms import PromotionForm, ScanForm
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


class ProtectedMediaTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser("media-user", "media@example.com", "Admin123")

    def test_protected_media_requires_login(self):
        response = self.client.get(reverse("protected-media", kwargs={"path": "products/cat.jpg"}))

        self.assertEqual(response.status_code, 302)

    @override_settings(USE_S3_MEDIA=False)
    def test_protected_media_serves_existing_file_to_dashboard_user(self):
        # This test exercises the local-filesystem branch of protected_media_view.
        # Without pinning USE_S3_MEDIA it inherits the environment's value, and in
        # an S3-mode container the view redirects to object storage where the temp
        # file does not exist — failing with 404 for reasons unrelated to the view.
        self.client.force_login(self.user)

        with TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            product_dir = os.path.join(media_root, "products")
            os.makedirs(product_dir, exist_ok=True)
            with open(os.path.join(product_dir, "cat.jpg"), "wb") as handle:
                handle.write(b"saved-image")

            response = self.client.get(reverse("protected-media", kwargs={"path": "products/cat.jpg"}))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(b"".join(response.streaming_content), b"saved-image")

    @override_settings(USE_S3_MEDIA=True)
    @mock.patch("core.views.default_storage")
    def test_protected_media_redirects_to_signed_storage_url_when_s3_media_enabled(self, storage):
        storage.exists.return_value = True
        storage.url.return_value = "https://media.example.com/melodu-media/products/cat.jpg?signature=abc"
        self.client.force_login(self.user)

        response = self.client.get(reverse("protected-media", kwargs={"path": "products/cat.jpg"}))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], storage.url.return_value)
        storage.exists.assert_called_once_with("products/cat.jpg")


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
        self.assertContains(response, "Store Settings")
        self.assertContains(response, "Login &amp; Authentication")
        self.assertContains(response, "Style Guide")
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


class TranslationCoverageTests(TestCase):
    def test_khmer_translates_v7_staff_facing_terms(self):
        expected = {
            "Stock Overview": "ទិដ្ឋភាពស្តុក",
            "Scan Barcode or QR": "ស្កេនបាកូដ ឬ QR",
            "What to do next": "អ្វីត្រូវធ្វើបន្ទាប់",
            "Choose an active product with an original barcode. Use Scan Product to fill this field faster.": (
                "ជ្រើសផលិតផលសកម្មដែលមានបាកូដដើម។ ប្រើ ស្កេនផលិតផល ដើម្បីបំពេញវាលនេះឱ្យលឿន។"
            ),
            "Choose the layout used for every selected batch.": "ជ្រើសប្លង់សម្រាប់ Batch ដែលបានជ្រើសទាំងអស់។",
            "Percentage, fixed amount off, or fixed final price.": "ភាគរយ បញ្ចុះចំនួនថេរ ឬតម្លៃចុងក្រោយថេរ។",
        }

        with override("km"):
            for source, translated in expected.items():
                self.assertEqual(gettext(source), translated)

    def test_v7_python_form_copy_uses_gettext_wrappers(self):
        with override("km"):
            stock_form = StockInForm()
            scan_form = ScanForm()
            label_form = TemplateLabelPrintForm()
            promotion_form = PromotionForm()

            self.assertEqual(scan_form.fields["scan_value"].label, "ស្កេនបាកូដ ឬ QR")
            self.assertIn("បាកូដដើម", str(stock_form.fields["product"].help_text))
            self.assertIn("ប្លង់", str(label_form.fields["template"].help_text))
            self.assertIn("ភាគរយ", str(promotion_form.fields["discount_type"].help_text))


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
        self.assertContains(response, "Print Labels")
        self.assertNotContains(response, "Open POS")

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
        self.assertNotContains(response, "Batch Upload")
        self.assertNotContains(response, "Print Labels")

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
        self.assertContains(response, "What to do next", status_code=403)
        self.assertContains(response, "ask an Owner to update your role", status_code=403)
        self.assertContains(response, "AUDIT TRAIL ACTIVE", status_code=403)
        self.assertNotContains(response, "EVENT LOGGED", status_code=403)

    @override_settings(DEBUG=False, ALLOWED_HOSTS=["testserver"])
    def test_missing_dashboard_object_renders_friendly_404(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse("product-edit", kwargs={"product_id": 999999}))

        self.assertEqual(response.status_code, 404)
        self.assertContains(response, "Page or item not found", status_code=404)
        self.assertContains(response, "Check that the link is current", status_code=404)
        self.assertContains(response, "NO TECHNICAL DETAILS SHOWN", status_code=404)

    def test_server_error_handler_renders_friendly_500(self):
        request = RequestFactory().get("/dashboard/error/")
        request.user = AnonymousUser()

        response = dashboard_server_error_view(request)

        self.assertEqual(response.status_code, 500)
        self.assertIn(b"Unexpected error", response.content)
        self.assertIn(b"System Health and Live Logs", response.content)
        self.assertIn(b"NO TECHNICAL DETAILS SHOWN", response.content)


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

    @mock.patch("core.views._decode_scan_image", return_value="8851234567890")
    def test_scan_decode_image_endpoint_returns_decoded_code(self, decode_image):
        self.client.force_login(self.admin)
        upload = SimpleUploadedFile("scan.jpg", b"fake-image", content_type="image/jpeg")

        response = self.client.post(reverse("scan-decode-image"), {"image": upload})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["code"], "8851234567890")
        decode_image.assert_called_once()

    def test_scan_decode_image_endpoint_requires_login(self):
        upload = SimpleUploadedFile("scan.jpg", b"fake-image", content_type="image/jpeg")

        response = self.client.post(reverse("scan-decode-image"), {"image": upload})

        self.assertEqual(response.status_code, 302)

    def test_scan_decode_image_endpoint_requires_file(self):
        self.client.force_login(self.admin)

        response = self.client.post(reverse("scan-decode-image"), {})

        self.assertEqual(response.status_code, 400)


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
        self.assertContains(pos_response, "Best results")

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

    def test_scanner_asset_enables_mobile_barcode_decode_options(self):
        scanner_js = settings.BASE_DIR / "core" / "static" / "core" / "js" / "scanner.js"
        source = scanner_js.read_text()

        self.assertIn("Html5QrcodeSupportedFormats", source)
        self.assertIn("useBarCodeDetectorIfSupported: true", source)
        self.assertIn("F.EAN_13", source)
        self.assertIn("F.CODE_128", source)
        self.assertIn("qrbox: function", source)
        self.assertIn("BarcodeDetector", source)
        self.assertIn("normalizeImageFile", source)
        self.assertIn("scanFileWithServer", source)
        self.assertIn("/dashboard/api/scan/decode-image/", source)
        self.assertIn("Math.floor(viewfinderHeight * 0.72)", source)
        self.assertIn('facingMode: { exact: "environment" }', source)

    def test_dashboard_css_contains_mobile_usability_guards(self):
        dashboard_css = settings.BASE_DIR / "core" / "static" / "core" / "css" / "dashboard.css"
        source = dashboard_css.read_text()

        self.assertIn("V7-010: mobile/tablet usability guards", source)
        self.assertIn(".table-scroll:not(.pos-cart-scroll) > .data-table { min-width: 720px; }", source)
        self.assertIn("body.auth-page", source)
        self.assertIn("overflow: auto", source)
        self.assertIn(".scanner-panel", source)
        self.assertIn(".scanner-help", source)
        self.assertIn("max-height: 100dvh", source)
        self.assertIn(".payment-methods", source)
        self.assertIn("grid-template-columns: repeat(2, 1fr)", source)
        self.assertIn(".mobile-nav a span", source)


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
                "khr_exchange_rate": 4100,
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
                "khr_exchange_rate": 4100,
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


class StyleguideAccessTests(TestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_superuser("sg-owner", "o@x.com", "Admin123")
        self.cashier = get_user_model().objects.create_user("sg-cashier", password="Admin123")
        StaffProfile.objects.create(user=self.cashier, role="CASHIER")

    def test_owner_can_open_styleguide_and_it_renders_components(self):
        self.client.force_login(self.owner)
        response = self.client.get(reverse("styleguide"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Living Style Guide")
        self.assertContains(response, "Color tokens")
        self.assertContains(response, 'id="tokens"')
        self.assertContains(response, 'id="buttons"')
        self.assertContains(response, 'id="pills"')
        self.assertContains(response, "bg-primary")
        self.assertContains(response, "--bg")

    def test_cashier_cannot_open_styleguide(self):
        self.client.force_login(self.cashier)
        response = self.client.get(reverse("styleguide"))
        self.assertEqual(response.status_code, 403)


class RoleMatrixTests(TestCase):
    """Authz Phase 2: the Owner-only role permission editor."""

    def setUp(self):
        self.owner = get_user_model().objects.create_superuser("rm-owner", "o@x.com", "Admin123")
        self.manager = get_user_model().objects.create_user("rm-manager", password="x")
        StaffProfile.objects.create(user=self.manager, role="MANAGER")
        self.cashier = get_user_model().objects.create_user("rm-cashier", password="x")
        StaffProfile.objects.create(user=self.cashier, role="CASHIER")

    def _post_data_from_current(self):
        """Build a POST mirroring the rendered checkboxes (all currently-granted
        capabilities checked) so we can tweak one and submit."""
        from accounts.models import Role
        from core.capabilities import ALL_CAPABILITIES

        data = {}
        for role in Role.objects.all():
            if role.is_owner:
                continue
            for cap in ALL_CAPABILITIES:
                if cap in (role.capabilities or []):
                    data[f"cap__{role.slug}__{cap}"] = "on"
        return data

    def test_owner_can_open_matrix_manager_cannot(self):
        self.client.force_login(self.manager)
        self.assertEqual(self.client.get(reverse("role-matrix")).status_code, 403)
        self.client.force_login(self.owner)
        response = self.client.get(reverse("role-matrix"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Permission matrix")

    def test_granting_capability_changes_access_and_audits(self):
        from core.permissions import can_cancel_sale

        cashier = get_user_model().objects.get(pk=self.cashier.pk)
        self.assertFalse(can_cancel_sale(cashier))

        self.client.force_login(self.owner)
        data = self._post_data_from_current()
        data["cap__CASHIER__sales.cancel"] = "on"  # grant cancel to cashiers
        response = self.client.post(reverse("role-matrix"), data)
        self.assertEqual(response.status_code, 302)

        cashier = get_user_model().objects.get(pk=self.cashier.pk)
        self.assertTrue(can_cancel_sale(cashier))
        self.assertTrue(
            AuditLog.objects.filter(action=AuditLog.Action.ROLE_CHANGE, object_display="Cashier").exists()
        )

    def test_revoking_capability_removes_access(self):
        from core.permissions import can_view_reports

        self.client.force_login(self.owner)
        data = self._post_data_from_current()
        data.pop("cap__MANAGER__reports.view", None)  # untick reports for managers
        self.client.post(reverse("role-matrix"), data)

        manager = get_user_model().objects.get(pk=self.manager.pk)
        self.assertFalse(can_view_reports(manager))

    def test_owner_role_cannot_be_limited(self):
        from accounts.models import Role
        from core.permissions import can_reset_data

        self.client.force_login(self.owner)
        # Submit with no owner checkboxes at all.
        self.client.post(reverse("role-matrix"), self._post_data_from_current())

        owner_role = Role.objects.get(slug="OWNER")
        self.assertTrue(owner_role.is_owner)
        self.assertTrue(can_reset_data(self.owner))


class AuthSettingsTests(TestCase):
    """Authz Phase 5: Owner-only login & auth settings."""

    def setUp(self):
        self.owner = get_user_model().objects.create_superuser("as-owner", "o@x.com", "Admin123")
        self.manager = get_user_model().objects.create_user("as-manager", password="x")
        StaffProfile.objects.create(user=self.manager, role="MANAGER")

    def test_owner_only_access(self):
        self.client.force_login(self.manager)
        self.assertEqual(self.client.get(reverse("auth-settings")).status_code, 403)
        self.client.force_login(self.owner)
        self.assertEqual(self.client.get(reverse("auth-settings")).status_code, 200)

    def test_owner_updates_settings_and_audits(self):
        from core.models import AuthSetting

        self.client.force_login(self.owner)
        response = self.client.post(
            reverse("auth-settings"),
            {"session_timeout_minutes": "120"},  # local_login_enabled unticked
        )
        self.assertEqual(response.status_code, 302)
        setting = AuthSetting.load()
        self.assertEqual(setting.session_timeout_minutes, 120)
        self.assertFalse(setting.local_login_enabled)
        self.assertTrue(AuditLog.objects.filter(action=AuditLog.Action.SETTING_CHANGE, object_display="Authentication settings").exists())

    def test_local_login_stays_available_without_oidc(self):
        # With OIDC off, disabling local login must NOT hide the form (no lockout).
        from core.models import AuthSetting

        s = AuthSetting.load()
        s.local_login_enabled = False
        s.save()
        response = self.client.get(reverse("dashboard-login"))
        self.assertContains(response, 'name="password"')


class DevAuthBypassGuardTests(SimpleTestCase):
    """The bypass must be impossible to activate outside local dev.

    These tests call the REAL guard used by settings.py — ``dev_auth_bypass_active``
    — not a copy, so weakening the guard fails a test rather than shipping.
    """

    def _guard(self, *, debug, bypass=True, hosts):
        from core.dev_auth import dev_auth_bypass_active

        return dev_auth_bypass_active(debug, bypass, hosts)

    def test_off_returns_false_without_raising(self):
        self.assertFalse(self._guard(debug=True, bypass=False, hosts=["melodu-pos.khlovepet.com"]))

    def test_refuses_when_debug_false(self):
        with self.assertRaises(ImproperlyConfigured):
            self._guard(debug=False, hosts=["localhost"])

    def test_refuses_production_host(self):
        with self.assertRaises(ImproperlyConfigured):
            self._guard(debug=True, hosts=["melodu-pos.khlovepet.com"])

    def test_refuses_sit_media_host(self):
        with self.assertRaises(ImproperlyConfigured):
            self._guard(debug=True, hosts=["mld-pos-media.khapper.com"])

    def test_refuses_wildcard(self):
        with self.assertRaises(ImproperlyConfigured):
            self._guard(debug=True, hosts=["*"])

    def test_refuses_public_ip(self):
        with self.assertRaises(ImproperlyConfigured):
            self._guard(debug=True, hosts=["192.168.1.212"])

    def test_refuses_uppercase_production_host(self):
        with self.assertRaises(ImproperlyConfigured):
            self._guard(debug=True, hosts=["MELODU-POS.KHLOVEPET.COM"])

    def test_refuses_trailing_dot_production_host(self):
        with self.assertRaises(ImproperlyConfigured):
            self._guard(debug=True, hosts=["melodu-pos.khlovepet.com."])

    def test_refuses_local_mixed_with_public(self):
        with self.assertRaises(ImproperlyConfigured):
            self._guard(debug=True, hosts=["localhost", "melodu-pos.khlovepet.com"])

    def test_refuses_empty_hosts(self):
        with self.assertRaises(ImproperlyConfigured):
            self._guard(debug=True, hosts=[])

    def test_allows_loopback_only(self):
        self.assertTrue(self._guard(debug=True, hosts=["localhost", "127.0.0.1", "web"]))

    def test_allows_loopback_with_whitespace_and_case(self):
        self.assertTrue(self._guard(debug=True, hosts=[" LOCALHOST ", "127.0.0.1"]))

    def test_middleware_not_installed_by_default(self):
        self.assertNotIn("core.dev_auth.DevAuthBypassMiddleware", settings.MIDDLEWARE)

    def test_is_running_tests_detects_test_argv(self):
        from core.dev_auth import is_running_tests

        self.assertTrue(is_running_tests(["manage.py", "test"]))
        self.assertTrue(is_running_tests(["manage.py", "test", "core"]))
        self.assertFalse(is_running_tests(["manage.py", "runserver"]))
        self.assertFalse(is_running_tests(["gunicorn", "melodu_pos.wsgi"]))


class DevAuthBypassMiddlewareTests(TestCase):
    def test_self_disables_when_inactive(self):
        from django.core.exceptions import MiddlewareNotUsed
        from core.dev_auth import DevAuthBypassMiddleware

        # DEBUG/DEV_AUTH_BYPASS are off in test settings → must refuse to install.
        with self.assertRaises(MiddlewareNotUsed):
            DevAuthBypassMiddleware(lambda r: r)

    def _make_middleware(self, trusted, dev_user):
        """Build the middleware bypassing __init__'s inactive guard, so the
        per-request peer logic can be tested directly."""
        from core.dev_auth import DevAuthBypassMiddleware

        mw = DevAuthBypassMiddleware.__new__(DevAuthBypassMiddleware)
        mw.get_response = lambda r: r
        mw._username = dev_user
        mw._trusted = frozenset(trusted)
        return mw

    def test_untrusted_peer_is_not_authenticated(self):
        # The reviewer's exploit: a remote client (203.0.113.9) sending
        # Host: localhost. REMOTE_ADDR is the real peer and is not trusted, so
        # the request must fall through unauthenticated.
        admin = get_user_model().objects.create_superuser("bypassadmin", "b@x.com", "Pw12345678")
        mw = self._make_middleware(trusted={"127.0.0.1"}, dev_user="")
        request = RequestFactory().get("/dashboard/", REMOTE_ADDR="203.0.113.9", HTTP_HOST="localhost")
        request.user = AnonymousUser()
        mw(request)
        self.assertFalse(request.user.is_authenticated)

    def test_trusted_loopback_peer_is_authenticated(self):
        admin = get_user_model().objects.create_superuser("bypassadmin2", "b2@x.com", "Pw12345678")
        mw = self._make_middleware(trusted={"127.0.0.1"}, dev_user="")
        request = RequestFactory().get("/dashboard/", REMOTE_ADDR="127.0.0.1")
        request.user = AnonymousUser()
        mw(request)
        self.assertTrue(request.user.is_authenticated)
        self.assertEqual(request.user, admin)
