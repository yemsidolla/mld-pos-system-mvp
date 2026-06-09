from datetime import date, timedelta
from decimal import Decimal
from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from audit.models import AuditLog
from catalog.models import Product, Supplier
from core.permissions import CASHIER_GROUP
from inventory.models import InventoryMovement, StockBatch
from inventory.services import receive_stock

from .models import Sale, SaleItem
from .services import cancel_sale, confirm_sale, parse_custom_code, scan_code


class PosServiceTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="cashier", password="Admin123", is_staff=True)
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
                received_by=self.user,
            )
        return StockBatch.objects.get(pk=stock_batch.pk)

    def test_custom_code_parser_works(self):
        parsed = parse_custom_code("8851234567890-M-270601-B260001")

        self.assertEqual(parsed.original_barcode, "8851234567890")
        self.assertEqual(parsed.indicator, "M")
        self.assertEqual(parsed.expiry_yymmdd, "270601")
        self.assertEqual(parsed.batch_no, "B260001")

    def test_original_barcode_scan_requires_batch_selection(self):
        stock_batch = self.create_batch()

        result = scan_code("8851234567890")

        self.assertEqual(result["scan_type"], "ORIGINAL_BARCODE")
        self.assertTrue(result["requires_batch_selection"])
        self.assertEqual(result["available_batches"], [stock_batch])

    def test_custom_code_scan_finds_exact_batch(self):
        stock_batch = self.create_batch()

        result = scan_code(stock_batch.custom_code)

        self.assertEqual(result["scan_type"], "CUSTOM_CODE")
        self.assertFalse(result["requires_batch_selection"])
        self.assertEqual(result["stock_batch"], stock_batch)

    def test_expired_batch_cannot_be_sold(self):
        stock_batch = self.create_batch(expiry_date=timezone.localdate() - timedelta(days=1))
        stock_batch.status = StockBatch.Status.ACTIVE
        stock_batch.save(update_fields=["status"])

        with self.assertRaises(ValidationError):
            scan_code(stock_batch.custom_code)

    def test_sale_deducts_from_correct_batch_and_creates_records(self):
        stock_batch = self.create_batch(quantity=10)

        sale = confirm_sale(
            cart_items=[{"stock_batch": stock_batch, "quantity": 3}],
            cashier=self.user,
            payment_method=Sale.PaymentMethod.CASH,
        )
        stock_batch.refresh_from_db()

        self.assertEqual(stock_batch.quantity_available, 7)
        self.assertEqual(sale.items.count(), 1)
        self.assertEqual(sale.items.get().stock_batch, stock_batch)
        self.assertTrue(InventoryMovement.objects.filter(movement_type=InventoryMovement.MovementType.SALE).exists())
        self.assertTrue(AuditLog.objects.filter(action=AuditLog.Action.SALE_CREATE).exists())

    def test_stock_cannot_become_negative(self):
        stock_batch = self.create_batch(quantity=2)

        with self.assertRaises(ValidationError):
            confirm_sale(
                cart_items=[{"stock_batch": stock_batch, "quantity": 3}],
                cashier=self.user,
            )

        stock_batch.refresh_from_db()
        self.assertEqual(stock_batch.quantity_available, 2)

    def test_sale_item_requires_stock_batch(self):
        sale = Sale.objects.create(sale_no="S2606060001", cashier=self.user)

        with self.assertRaises(Exception):
            SaleItem.objects.create(
                sale=sale,
                product=self.product,
                stock_batch=None,
                quantity=1,
                unit_price=Decimal("2.50"),
                subtotal=Decimal("2.50"),
            )


class PosPageTests(TestCase):
    def setUp(self):
        self.cashier = get_user_model().objects.create_user(username="page-cashier", password="Admin123")
        self.cashier.groups.add(Group.objects.get(name=CASHIER_GROUP))
        self.supplier = Supplier.objects.create(name="Pet Wholesale")
        self.product = Product.objects.create(
            product_code="P001",
            original_barcode="8851234567890",
            name="Cat Food",
            default_cost_price=Decimal("1.50"),
            default_selling_price=Decimal("2.50"),
        )

    def create_batch(self, quantity=5):
        with TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            stock_batch, _movement = receive_stock(
                product=self.product,
                supplier=self.supplier,
                quantity=quantity,
                expiry_date=date(2027, 6, 1),
                cost_price=Decimal("1.50"),
                selling_price=Decimal("2.50"),
                received_by=self.cashier,
            )
        return StockBatch.objects.get(pk=stock_batch.pk)

    def test_staff_can_open_pos_page(self):
        self.client.force_login(self.cashier)

        response = self.client.get(reverse("pos-sale"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "POS Sale")
        self.assertContains(response, "Ready for the next barcode")
        self.assertContains(response, "Cart is empty. Add a sellable batch before checkout.")
        self.assertContains(response, "data-disable-on-submit")
        self.assertContains(response, "Complete Sale")

    def test_anonymous_user_is_redirected_from_pos_page(self):
        response = self.client.get(reverse("pos-sale"))

        self.assertRedirects(response, f"{reverse('dashboard-login')}?next={reverse('pos-sale')}")

    def test_scan_post_without_action_still_looks_up_item(self):
        stock_batch = self.create_batch()
        self.client.force_login(self.cashier)

        response = self.client.post(reverse("pos-sale"), {"scan_value": self.product.original_barcode})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, stock_batch.batch_no)

    def test_cart_rejects_total_quantity_above_available(self):
        stock_batch = self.create_batch(quantity=2)
        self.client.force_login(self.cashier)

        self.client.post(
            reverse("pos-sale"),
            {"action": "add_batch", "stock_batch_id": stock_batch.id, "quantity": "2"},
        )
        response = self.client.post(
            reverse("pos-sale"),
            {"action": "add_batch", "stock_batch_id": stock_batch.id, "quantity": "1"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Not enough stock available.")
        self.assertEqual(self.client.session["pos_cart"][0]["quantity"], 2)

    def test_cart_quantity_can_be_updated_and_removed(self):
        stock_batch = self.create_batch(quantity=5)
        self.client.force_login(self.cashier)

        self.client.post(
            reverse("pos-sale"),
            {"action": "add_batch", "stock_batch_id": stock_batch.id, "quantity": "1"},
        )
        self.client.post(
            reverse("pos-sale"),
            {"action": "update_item", "stock_batch_id": stock_batch.id, "quantity": "3"},
        )
        self.assertEqual(self.client.session["pos_cart"][0]["quantity"], 3)

        self.client.post(reverse("pos-sale"), {"action": "remove_item", "stock_batch_id": stock_batch.id})
        self.assertEqual(self.client.session["pos_cart"], [])


class SalesCancellationTests(TestCase):
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
        )
        self.cashier.groups.add(Group.objects.get(name=CASHIER_GROUP))
        self.supplier = Supplier.objects.create(name="Pet Wholesale")
        self.product = Product.objects.create(
            product_code="P001",
            original_barcode="8851234567890",
            name="Cat Food",
            default_cost_price=Decimal("1.50"),
            default_selling_price=Decimal("2.50"),
        )

    def create_sale(self):
        with TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            stock_batch, _movement = receive_stock(
                product=self.product,
                supplier=self.supplier,
                quantity=5,
                expiry_date=date(2027, 6, 1),
                cost_price=Decimal("1.50"),
                selling_price=Decimal("2.50"),
                received_by=self.admin,
            )
        stock_batch = StockBatch.objects.get(pk=stock_batch.pk)
        sale = confirm_sale(
            cart_items=[{"stock_batch": stock_batch, "quantity": 2}],
            cashier=self.cashier,
        )
        return sale, stock_batch

    def test_cancel_sale_returns_stock_to_original_batch(self):
        sale, stock_batch = self.create_sale()
        stock_batch.refresh_from_db()
        self.assertEqual(stock_batch.quantity_available, 3)

        cancel_sale(sale=sale, cancelled_by=self.admin, reason="Mistake")
        stock_batch.refresh_from_db()
        sale.refresh_from_db()

        self.assertEqual(stock_batch.quantity_available, 5)
        self.assertEqual(sale.status, Sale.Status.CANCELLED)
        self.assertTrue(InventoryMovement.objects.filter(movement_type=InventoryMovement.MovementType.RETURN).exists())
        self.assertTrue(AuditLog.objects.filter(action=AuditLog.Action.SALE_CANCEL).exists())

    def test_cancel_sale_requires_reason(self):
        sale, _stock_batch = self.create_sale()

        with self.assertRaises(ValidationError):
            cancel_sale(sale=sale, cancelled_by=self.admin, reason="")

    def test_sales_history_and_detail_are_visible_to_admin(self):
        sale, _stock_batch = self.create_sale()
        self.client.force_login(self.admin)

        history = self.client.get(reverse("sales-history"), {"payment_method": Sale.PaymentMethod.CASH})
        detail = self.client.get(reverse("sale-detail", kwargs={"sale_id": sale.id}))

        self.assertEqual(history.status_code, 200)
        self.assertContains(history, sale.sale_no)
        self.assertEqual(detail.status_code, 200)
        self.assertContains(detail, "Cancel Sale")

    def test_cashier_cannot_cancel_sale(self):
        sale, _stock_batch = self.create_sale()
        self.client.force_login(self.cashier)

        response = self.client.post(reverse("sale-cancel", kwargs={"sale_id": sale.id}), {"reason": "No permission"})

        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "Access denied", status_code=403)
        sale.refresh_from_db()
        self.assertEqual(sale.status, Sale.Status.COMPLETED)
