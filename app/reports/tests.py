from datetime import date, timedelta
from decimal import Decimal
from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from catalog.models import Product, Supplier
from accounts.models import StaffProfile
from audit.models import AuditLog
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
        StaffProfile.objects.create(user=self.cashier, role=StaffProfile.Role.CASHIER)
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
                actual_unit_cost=Decimal("1.50"),
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
        self.assertContains(response, "All Reports")
        self.assertContains(response, "Staff Sales")
        self.assertContains(response, timezone.localdate().isoformat())
        self.assertContains(response, "Report Definition")
        self.assertContains(response, "Completed Sales")
        self.assertContains(response, "Cancelled Sales")
        self.assertContains(response, "Payment Breakdown")
        self.assertContains(response, "Gross Sales")
        self.assertContains(response, "Discounts")
        self.assertContains(response, "Completed Revenue")
        self.assertContains(response, "Cost of Goods")
        self.assertContains(response, "Gross Margin")
        self.assertEqual(response.context["totals"]["sale_count"], 1)
        self.assertEqual(response.context["totals"]["cancelled_count"], 0)
        self.assertEqual(response.context["payment_rows"][0]["label"], "Cash")

    def test_daily_sales_report_tracks_cancelled_sales_as_exceptions(self):
        Sale.objects.create(
            sale_no="S2606169999",
            cashier=self.cashier,
            total_amount=Decimal("9.00"),
            discount_amount=Decimal("0.00"),
            final_amount=Decimal("9.00"),
            payment_method=Sale.PaymentMethod.ABA,
            status=Sale.Status.CANCELLED,
            cancel_reason="Customer changed mind",
        )

        response = self.client.get(reverse("daily-sales-report"), {"date": timezone.localdate().isoformat()})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cancelled sales are exception records")
        self.assertEqual(response.context["totals"]["sale_count"], 1)
        self.assertEqual(response.context["totals"]["cancelled_count"], 1)
        self.assertEqual(response.context["totals"]["total_amount"], self.sale.final_amount)

    def test_daily_sales_invalid_date_falls_back_with_message(self):
        response = self.client.get(reverse("daily-sales-report"), {"date": "not-a-date"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid report date")

    def test_stock_summary_report_shows_product(self):
        response = self.client.get(reverse("stock-summary-report"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cat Food")
        self.assertContains(response, "Products")
        self.assertContains(response, "Available Units")
        self.assertContains(response, "Reorder Units")
        self.assertContains(response, "Report Definition")
        self.assertContains(response, "Out of Stock")
        self.assertContains(response, "Healthy")
        self.assertContains(response, "Reorder Gap")
        self.assertContains(response, "Level")
        self.assertContains(response, "Low stock")
        self.assertContains(response, "Open Stock")
        self.assertEqual(response.context["summary"]["product_count"], 1)
        self.assertEqual(response.context["summary"]["reorder_units"], 7)
        self.assertEqual(response.context["summary"]["out_of_stock_count"], 0)

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
        self.assertContains(response, "Low-stock Products")
        self.assertContains(response, "Reorder Units")
        self.assertContains(response, "Report Definition")
        self.assertContains(response, "Out of Stock")
        self.assertContains(response, "Reorder Gap")
        self.assertContains(response, "Open Stock")
        self.assertContains(response, "Receive Stock")
        self.assertEqual(response.context["summary"]["product_count"], 1)
        self.assertEqual(response.context["products"][0].reorder_gap, 7)

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
        self.assertContains(response, "Days")
        self.assertContains(response, "Review today")
        self.assertContains(response, "Report Definition")
        self.assertContains(response, "Review Now")
        self.assertContains(response, "Open Batch")
        self.assertContains(response, self.supplier.name)
        self.assertContains(response, "Batches")
        self.assertContains(response, reverse("stock-batch-detail", kwargs={"batch_id": self.stock_batch.id}))
        self.assertEqual(response.context["summary"]["critical_count"], 1)
        self.assertEqual(response.context["summary"]["review_now_count"], 1)

    def test_expiry_report_excludes_non_active_batches(self):
        self.stock_batch.status = StockBatch.Status.SOLD_OUT
        self.stock_batch.save(update_fields=["status", "updated_at"])

        response = self.client.get(reverse("expiry-report"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, self.stock_batch.batch_no)

    def test_stock_movement_report_can_trace_movements(self):
        response = self.client.get(reverse("stock-movement-report"))

        self.assertEqual(response.status_code, 200)
        # The report renders the human-readable movement type label ("Sale").
        self.assertContains(response, InventoryMovement.MovementType.SALE.label)
        self.assertContains(response, "Movements")
        self.assertContains(response, "Trace Filters")
        self.assertContains(response, "Search stock movement trace")
        self.assertContains(response, "Stock Overview")
        self.assertContains(response, "Inventory Audit Logs")
        self.assertContains(response, self.stock_batch.custom_code)
        self.assertContains(response, reverse("stock-batch-detail", kwargs={"batch_id": self.stock_batch.id}))
        self.assertContains(response, "Sale")
        self.assertGreaterEqual(response.context["movement_count"], 1)

        filtered = self.client.get(
            reverse("stock-movement-report"),
            {"q": self.stock_batch.custom_code, "movement_type": InventoryMovement.MovementType.SALE},
        )
        self.assertEqual(filtered.status_code, 200)
        self.assertContains(filtered, self.stock_batch.batch_no)
        self.assertEqual(filtered.context["movement_type"], InventoryMovement.MovementType.SALE)

    def test_staff_sales_report_shows_cashier_sales(self):
        AuditLog.objects.create(
            action=AuditLog.Action.RECEIPT_PRINT,
            module="pos",
            user=self.admin,
            object_type="Sale",
            object_id=str(self.sale.pk),
            object_display=self.sale.sale_no,
        )
        response = self.client.get(reverse("staff-sales-report"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "cashier")
        self.assertContains(response, "Completed Sales")
        self.assertContains(response, "Cashier Accountability")
        self.assertContains(response, "Cancelled Sales")
        self.assertContains(response, "Receipt Reprints")
        self.assertContains(response, "Below-cost Overrides")
        self.assertContains(response, "Average Sale")
        self.assertContains(response, "Discounts")
        self.assertContains(response, "Cost of Goods")
        self.assertContains(response, "Gross Margin")
        self.assertContains(response, "Total Sales")
        self.assertEqual(response.context["summary"]["staff_count"], 1)
        self.assertEqual(response.context["summary"]["sale_count"], 1)
        self.assertEqual(response.context["summary"]["reprint_count"], 1)

    def test_staff_sales_report_counts_cancelled_sales_by_cashier(self):
        Sale.objects.create(
            sale_no="S2606169998",
            cashier=self.cashier,
            total_amount=Decimal("5.00"),
            final_amount=Decimal("5.00"),
            status=Sale.Status.CANCELLED,
            cancel_reason="Mistake",
        )

        response = self.client.get(reverse("staff-sales-report"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["summary"]["sale_count"], 1)
        self.assertEqual(response.context["summary"]["cancelled_count"], 1)

    def test_promotion_report_uses_sale_item_snapshots(self):
        item = self.sale.items.first()
        item.promotion_name_at_sale = "Cat Food Launch"
        item.original_unit_price = Decimal("2.50")
        item.final_unit_price = Decimal("1.00")
        item.discount_amount = Decimal("1.50")
        item.cost_basis_at_sale = Decimal("1.50")
        item.subtotal = Decimal("2.00")
        item.override_by = self.admin
        item.override_reason = "Owner approved launch promo"
        item.save(
            update_fields=[
                "promotion_name_at_sale",
                "original_unit_price",
                "final_unit_price",
                "discount_amount",
                "cost_basis_at_sale",
                "subtotal",
                "override_by",
                "override_reason",
            ]
        )

        response = self.client.get(reverse("promotion-report"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Promotion & Below-cost Report")
        self.assertContains(response, "Cat Food Launch")
        self.assertContains(response, "Promotion Impact")
        self.assertContains(response, "Below-cost Review")
        self.assertContains(response, "Cost of Goods")
        self.assertContains(response, "Gross Margin")
        self.assertEqual(response.context["summary"]["promotion_count"], 1)
        self.assertEqual(response.context["summary"]["below_cost_count"], 1)
        self.assertEqual(response.context["summary"]["override_count"], 1)

    def test_reports_index_links_to_promotion_report(self):
        response = self.client.get(reverse("reports-index"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Promotion & Below-cost Report")
        self.assertContains(response, reverse("promotion-report"))
        self.assertContains(response, "Daily Closing Checklist")
        self.assertContains(response, reverse("daily-closing-checklist"))

    def test_daily_closing_checklist_shows_evidence_links(self):
        response = self.client.get(reverse("daily-closing-checklist"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Daily Closing Checklist")
        self.assertContains(response, "Operating Rule")
        self.assertContains(response, "not accounting")
        self.assertContains(response, "Evidence Links")
        self.assertContains(response, reverse("daily-sales-report"))
        self.assertContains(response, reverse("staff-sales-report"))
        self.assertContains(response, reverse("promotion-report"))

    def test_cashier_cannot_view_reports(self):
        self.client.force_login(self.cashier)

        response = self.client.get(reverse("reports-index"))

        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "Access denied", status_code=403)
