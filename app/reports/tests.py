from datetime import date, timedelta
from decimal import Decimal
from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from catalog.models import Product, Supplier
from inventory.models import InventoryMovement, StockBatch
from inventory.services import receive_stock
from pos.models import Sale
from pos.services import confirm_sale


class ReportPageTests(TestCase):
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
        self.supplier = Supplier.objects.create(name="Pet Wholesale")
        self.product = Product.objects.create(
            product_code="P001",
            original_barcode="8851234567890",
            name="Cat Food",
            min_stock=10,
            default_cost_price=Decimal("1.50"),
            default_selling_price=Decimal("2.50"),
        )
        with TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            self.stock_batch, _movement = receive_stock(
                product=self.product,
                supplier=self.supplier,
                quantity=5,
                expiry_date=timezone.localdate() + timedelta(days=20),
                cost_price=Decimal("1.50"),
                selling_price=Decimal("2.50"),
                received_by=self.admin,
            )
        self.sale = confirm_sale(
            cart_items=[{"stock_batch": self.stock_batch, "quantity": 2}],
            cashier=self.cashier,
            payment_method=Sale.PaymentMethod.CASH,
        )
        self.client.force_login(self.admin)

    def test_daily_sales_report_shows_total(self):
        response = self.client.get(reverse("daily-sales-report"), {"date": timezone.localdate().isoformat()})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.sale.sale_no)
        self.assertContains(response, "Daily Sales Report")

    def test_stock_summary_report_shows_product(self):
        response = self.client.get(reverse("stock-summary-report"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cat Food")

    def test_stock_summary_counts_only_sellable_stock(self):
        self.stock_batch.expiry_date = timezone.localdate() - timedelta(days=1)
        self.stock_batch.save(update_fields=["expiry_date", "updated_at"])

        response = self.client.get(reverse("stock-summary-report"))

        self.assertEqual(response.status_code, 200)
        product = response.context["products"][0]
        self.assertEqual(product.total_available, 0)

    def test_low_stock_report_shows_low_stock_product(self):
        response = self.client.get(reverse("low-stock-report"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cat Food")

    def test_low_stock_report_excludes_inactive_products(self):
        self.product.is_active = False
        self.product.save(update_fields=["is_active", "updated_at"])

        response = self.client.get(reverse("low-stock-report"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Cat Food")

    def test_expiry_report_shows_near_expiry_batch(self):
        response = self.client.get(reverse("expiry-report"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.stock_batch.batch_no)
        self.assertContains(response, "Critical")

    def test_expiry_report_excludes_non_active_batches(self):
        self.stock_batch.status = StockBatch.Status.SOLD_OUT
        self.stock_batch.save(update_fields=["status", "updated_at"])

        response = self.client.get(reverse("expiry-report"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, self.stock_batch.batch_no)

    def test_stock_movement_report_can_trace_movements(self):
        response = self.client.get(reverse("stock-movement-report"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, InventoryMovement.MovementType.SALE)

    def test_staff_sales_report_shows_cashier_sales(self):
        response = self.client.get(reverse("staff-sales-report"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "cashier")

    def test_cashier_cannot_view_reports(self):
        self.client.force_login(self.cashier)

        response = self.client.get(reverse("reports-index"))

        self.assertEqual(response.status_code, 302)
