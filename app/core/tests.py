from datetime import date
from decimal import Decimal
from tempfile import TemporaryDirectory

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from batch_upload.models import BatchUploadJob, BatchUploadRow
from catalog.models import Product, Supplier
from core.permissions import CASHIER_GROUP
from inventory.models import StockBatch
from inventory.services import receive_stock


class HealthUrlTests(SimpleTestCase):
    def test_health_url_resolves(self):
        self.assertEqual(reverse("health-check"), "/health/")


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

    def test_language_settings_include_english_and_khmer(self):
        self.assertIn(("en", "English"), settings.LANGUAGES)
        self.assertIn(("km", "ភាសាខ្មែរ"), settings.LANGUAGES)

    def test_admin_dashboard_shows_admin_navigation(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse("dashboard-home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Melodu Dashboard")
        self.assertContains(response, "Batch Upload")
        self.assertContains(response, "Django Admin")

    def test_cashier_dashboard_hides_admin_navigation(self):
        self.client.force_login(self.cashier)

        response = self.client.get(reverse("dashboard-home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "POS")
        self.assertNotContains(response, "Batch Upload")


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
                cost_price=Decimal("1.50"),
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
