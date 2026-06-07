from decimal import Decimal
from tempfile import TemporaryDirectory
from datetime import date

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.urls import reverse

from audit.models import AuditLog
from catalog.models import Brand, Category, Product, Supplier

from .models import InventoryMovement, StockBatch
from .services import (
    adjust_stock,
    build_custom_code,
    get_expiry_status,
    mark_batch_damaged,
    mark_batch_expired,
    receive_stock,
)


class StockInServiceTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Food")
        self.brand = Brand.objects.create(name="Melodu")
        self.supplier = Supplier.objects.create(name="Pet Wholesale")
        self.user = get_user_model().objects.create_user(username="admin", password="Admin123", is_staff=True)
        self.product = Product.objects.create(
            product_code="P001",
            original_barcode="8851234567890",
            name="Cat Food",
            category=self.category,
            brand=self.brand,
            default_cost_price=Decimal("1.50"),
            default_selling_price=Decimal("2.50"),
        )

    def test_build_custom_code_uses_melodu_standard(self):
        custom_code = build_custom_code(self.product, date(2027, 6, 1), "B260001")

        self.assertEqual(custom_code, "8851234567890-M-270601-B260001")

    def test_stock_in_creates_batch_images_movement_and_audit(self):
        with TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            stock_batch, movement = receive_stock(
                product=self.product,
                supplier=self.supplier,
                quantity=10,
                expiry_date=date(2027, 6, 1),
                cost_price=Decimal("1.50"),
                selling_price=Decimal("2.50"),
                received_by=self.user,
            )

            self.assertEqual(stock_batch.batch_no[:3], "B26")
            self.assertEqual(stock_batch.quantity_received, 10)
            self.assertEqual(stock_batch.quantity_available, 10)
            self.assertEqual(stock_batch.status, StockBatch.Status.ACTIVE)
            self.assertEqual(stock_batch.custom_code, f"8851234567890-M-270601-{stock_batch.batch_no}")
            self.assertTrue(stock_batch.barcode_image.name.endswith(".png"))
            self.assertTrue(stock_batch.qr_image.name.endswith(".png"))
            self.assertEqual(movement.movement_type, InventoryMovement.MovementType.STOCK_IN)
            self.assertEqual(movement.quantity, 10)
            self.assertTrue(AuditLog.objects.filter(action=AuditLog.Action.STOCK_IN).exists())

    def test_stock_in_requires_product_original_barcode(self):
        self.product.original_barcode = None
        self.product.save(update_fields=["original_barcode"])

        with self.assertRaises(ValidationError):
            receive_stock(
                product=self.product,
                supplier=self.supplier,
                quantity=10,
                expiry_date=date(2027, 6, 1),
                cost_price=Decimal("1.50"),
                selling_price=Decimal("2.50"),
                received_by=self.user,
            )

    def test_stock_in_rejects_inactive_product(self):
        self.product.is_active = False
        self.product.save(update_fields=["is_active"])

        with self.assertRaises(ValidationError):
            receive_stock(
                product=self.product,
                supplier=self.supplier,
                quantity=10,
                expiry_date=date(2027, 6, 1),
                cost_price=Decimal("1.50"),
                selling_price=Decimal("2.50"),
                received_by=self.user,
            )

    def test_stock_batch_quantity_available_cannot_exceed_received(self):
        stock_batch = StockBatch(
            product=self.product,
            supplier=self.supplier,
            batch_no="B260001",
            expiry_date=date(2027, 6, 1),
            quantity_received=5,
            quantity_available=6,
            cost_price=Decimal("1.50"),
            selling_price=Decimal("2.50"),
            custom_code="8851234567890-M-270601-B260001",
            received_by=self.user,
        )

        with self.assertRaises(ValidationError):
            stock_batch.full_clean()


class StockInPageTests(TestCase):
    def test_staff_can_open_stock_in_page(self):
        user = get_user_model().objects.create_user(
            username="stock-admin",
            password="Admin123",
            is_staff=True,
            is_superuser=True,
        )
        self.client.force_login(user)

        response = self.client.get(reverse("stock-in"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Stock-In")

    def test_anonymous_user_is_redirected_from_stock_in_page(self):
        response = self.client.get(reverse("stock-in"))

        self.assertEqual(response.status_code, 302)


class BarcodePrintPageTests(TestCase):
    def setUp(self):
        self.supplier = Supplier.objects.create(name="Pet Wholesale")
        self.user = get_user_model().objects.create_user(
            username="label-admin",
            password="Admin123",
            is_staff=True,
            is_superuser=True,
        )
        self.product = Product.objects.create(
            product_code="P001",
            original_barcode="8851234567890",
            name="Cat Food",
            default_cost_price=Decimal("1.50"),
            default_selling_price=Decimal("2.50"),
        )

    def create_batch(self):
        stock_batch, _movement = receive_stock(
            product=self.product,
            supplier=self.supplier,
            quantity=10,
            expiry_date=date(2027, 6, 1),
            cost_price=Decimal("1.50"),
            selling_price=Decimal("2.50"),
            received_by=self.user,
        )
        return stock_batch

    def test_label_preview_includes_required_fields(self):
        self.client.force_login(self.user)
        with TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            stock_batch = self.create_batch()
            response = self.client.post(
                reverse("barcode-print"),
                {"stock_batch": stock_batch.pk, "label_quantity": 2, "action": "preview"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Melodu Pet Store", count=2)
        self.assertContains(response, "Cat Food")
        self.assertContains(response, "Price:")
        self.assertContains(response, "Expiry Date:")
        self.assertContains(response, "Batch Number:")
        self.assertContains(response, stock_batch.custom_code)

    def test_print_action_creates_audit_log(self):
        self.client.force_login(self.user)
        with TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            stock_batch = self.create_batch()
            response = self.client.post(
                reverse("barcode-print"),
                {"stock_batch": stock_batch.pk, "label_quantity": 3, "action": "print"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            AuditLog.objects.filter(
                action=AuditLog.Action.BARCODE_PRINT,
                object_id=str(stock_batch.pk),
            ).exists()
        )


class InventoryAdjustmentTests(TestCase):
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
            default_cost_price=Decimal("1.50"),
            default_selling_price=Decimal("2.50"),
        )

    def create_batch(self, quantity=10, expiry_date=None):
        expiry_date = expiry_date or date(2027, 6, 1)
        with TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            stock_batch, _movement = receive_stock(
                product=self.product,
                supplier=self.supplier,
                quantity=quantity,
                expiry_date=expiry_date,
                cost_price=Decimal("1.50"),
                selling_price=Decimal("2.50"),
                received_by=self.admin,
            )
        return StockBatch.objects.get(pk=stock_batch.pk)

    def test_stock_adjustment_works_and_creates_movement_and_audit(self):
        stock_batch = self.create_batch(quantity=10)

        adjust_stock(stock_batch=stock_batch, delta_quantity=-2, reason="Count correction", adjusted_by=self.admin)
        stock_batch.refresh_from_db()

        self.assertEqual(stock_batch.quantity_available, 8)
        self.assertTrue(InventoryMovement.objects.filter(movement_type=InventoryMovement.MovementType.ADJUSTMENT).exists())
        self.assertTrue(AuditLog.objects.filter(action=AuditLog.Action.STOCK_ADJUSTMENT).exists())

    def test_stock_adjustment_requires_reason(self):
        stock_batch = self.create_batch(quantity=10)

        with self.assertRaises(ValidationError):
            adjust_stock(stock_batch=stock_batch, delta_quantity=-1, reason="", adjusted_by=self.admin)

    def test_stock_adjustment_prevents_negative_stock(self):
        stock_batch = self.create_batch(quantity=3)

        with self.assertRaises(ValidationError):
            adjust_stock(stock_batch=stock_batch, delta_quantity=-4, reason="Bad count", adjusted_by=self.admin)

        stock_batch.refresh_from_db()
        self.assertEqual(stock_batch.quantity_available, 3)

    def test_expiry_status_values(self):
        self.assertEqual(get_expiry_status(self.create_batch(expiry_date=date(2027, 6, 1)), today=date(2026, 6, 1)), "Normal")
        self.assertEqual(get_expiry_status(self.create_batch(expiry_date=date(2026, 7, 20)), today=date(2026, 6, 1)), "Warning")
        self.assertEqual(get_expiry_status(self.create_batch(expiry_date=date(2026, 6, 20)), today=date(2026, 6, 1)), "Critical")
        self.assertEqual(get_expiry_status(self.create_batch(expiry_date=date(2026, 5, 20)), today=date(2026, 6, 1)), "Expired")

    def test_damaged_stock_creates_movement_and_audit(self):
        stock_batch = self.create_batch(quantity=5)

        mark_batch_damaged(stock_batch=stock_batch, quantity=2, reason="Broken package", marked_by=self.admin)
        stock_batch.refresh_from_db()

        self.assertEqual(stock_batch.quantity_available, 3)
        self.assertTrue(InventoryMovement.objects.filter(movement_type=InventoryMovement.MovementType.DAMAGE).exists())
        self.assertTrue(AuditLog.objects.filter(action=AuditLog.Action.STOCK_ADJUSTMENT).exists())

    def test_mark_expired_creates_movement_and_audit(self):
        stock_batch = self.create_batch(quantity=5)

        mark_batch_expired(stock_batch=stock_batch, reason="Expired on shelf", marked_by=self.admin)
        stock_batch.refresh_from_db()

        self.assertEqual(stock_batch.quantity_available, 0)
        self.assertEqual(stock_batch.status, StockBatch.Status.EXPIRED)
        self.assertTrue(InventoryMovement.objects.filter(movement_type=InventoryMovement.MovementType.EXPIRED).exists())
        self.assertTrue(AuditLog.objects.filter(action=AuditLog.Action.STOCK_ADJUSTMENT).exists())

    def test_inventory_pages_are_admin_only(self):
        stock_batch = self.create_batch(quantity=5)
        self.client.force_login(self.cashier)
        cashier_response = self.client.get(reverse("inventory-summary"))
        self.assertEqual(cashier_response.status_code, 302)

        self.client.force_login(self.admin)
        summary = self.client.get(reverse("inventory-summary"))
        detail = self.client.get(reverse("stock-batch-detail", kwargs={"batch_id": stock_batch.id}))

        self.assertEqual(summary.status_code, 200)
        self.assertContains(summary, "Product Stock Summary")
        self.assertEqual(detail.status_code, 200)
        self.assertContains(detail, "Expiry Status")
