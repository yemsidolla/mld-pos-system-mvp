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
from catalog.models import Category, Product, Supplier, SupplierProductCost
from core.permissions import CASHIER_GROUP
from inventory.models import InventoryMovement, StockBatch
from inventory.services import receive_stock

from .models import Promotion, Sale, SaleItem
from .services import cancel_sale, confirm_sale, parse_custom_code, scan_code


class PosServiceTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="cashier", password="Admin123", is_staff=True)
        self.admin = get_user_model().objects.create_user(
            username="manager",
            password="Admin123",
            is_staff=True,
            is_superuser=True,
        )
        self.category = Category.objects.create(name="Food")
        self.supplier = Supplier.objects.create(name="Pet Wholesale")
        self.product = Product.objects.create(
            product_code="P001",
            original_barcode="8851234567890",
            name="Cat Food",
            category=self.category,
            default_cost_price=Decimal("1.50"),
            default_selling_price=Decimal("2.50"),
        )

    def create_batch(self, quantity=10, expiry_date=None, actual_unit_cost=Decimal("1.50"), selling_price=Decimal("2.50"), landed_unit_cost=None):
        expiry_date = expiry_date or date(2027, 6, 1)
        kwargs = {}
        if landed_unit_cost is not None:
            kwargs["landed_unit_cost"] = landed_unit_cost
        with TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            stock_batch, _movement = receive_stock(
                product=self.product,
                supplier=self.supplier,
                quantity=quantity,
                expiry_date=expiry_date,
                actual_unit_cost=actual_unit_cost,
                selling_price=selling_price,
                received_by=self.user,
                **kwargs,
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

    def test_sale_item_snapshots_costs_prices_and_batch(self):
        stock_batch = self.create_batch(
            actual_unit_cost=Decimal("1.60"),
            landed_unit_cost=Decimal("1.85"),
            selling_price=Decimal("2.50"),
        )

        sale = confirm_sale(
            cart_items=[{"stock_batch": stock_batch, "quantity": 2}],
            cashier=self.user,
        )

        item = sale.items.get()
        self.assertEqual(item.stock_batch, stock_batch)
        self.assertEqual(item.reference_cost_at_sale, Decimal("1.50"))
        self.assertEqual(item.actual_cost_at_sale, Decimal("1.60"))
        self.assertEqual(item.landed_cost_at_sale, Decimal("1.85"))
        self.assertEqual(item.cost_basis_at_sale, Decimal("1.85"))
        self.assertEqual(item.original_unit_price, Decimal("2.50"))
        self.assertEqual(item.final_unit_price, Decimal("2.50"))
        self.assertEqual(item.discount_amount, Decimal("0.00"))
        self.assertEqual(item.subtotal, Decimal("5.00"))

    def test_cost_basis_falls_back_to_supplier_reference_when_batch_cost_is_zero(self):
        SupplierProductCost.objects.create(
            product=self.product,
            supplier=self.supplier,
            reference_unit_cost=Decimal("2.00"),
        )
        stock_batch = self.create_batch(actual_unit_cost=Decimal("0.00"), selling_price=Decimal("2.10"))

        sale = confirm_sale(
            cart_items=[{"stock_batch": stock_batch, "quantity": 1}],
            cashier=self.user,
        )

        self.assertEqual(sale.items.get().reference_cost_at_sale, Decimal("2.00"))
        self.assertEqual(sale.items.get().cost_basis_at_sale, Decimal("2.00"))

    def test_cashier_cannot_sell_below_cost(self):
        stock_batch = self.create_batch(actual_unit_cost=Decimal("2.50"), selling_price=Decimal("2.00"))

        with self.assertRaisesMessage(ValidationError, "Manager approval required for this price."):
            confirm_sale(
                cart_items=[{"stock_batch": stock_batch, "quantity": 1}],
                cashier=self.user,
            )

        stock_batch.refresh_from_db()
        self.assertEqual(stock_batch.quantity_available, 10)
        self.assertEqual(Sale.objects.count(), 0)

    def test_admin_override_below_cost_requires_reason_and_is_audited(self):
        stock_batch = self.create_batch(actual_unit_cost=Decimal("2.50"), selling_price=Decimal("2.00"))

        with self.assertRaisesMessage(ValidationError, "Override reason is required for below-cost sale."):
            confirm_sale(
                cart_items=[{"stock_batch": stock_batch, "quantity": 1}],
                cashier=self.admin,
            )

        sale = confirm_sale(
            cart_items=[{"stock_batch": stock_batch, "quantity": 1}],
            cashier=self.admin,
            override_reason="Manager approved clearance price",
        )

        item = sale.items.get()
        self.assertEqual(item.override_by, self.admin)
        self.assertEqual(item.override_reason, "Manager approved clearance price")
        self.assertTrue(AuditLog.objects.filter(action=AuditLog.Action.BELOW_COST_SALE, object_id=sale.pk).exists())
        self.assertTrue(AuditLog.objects.filter(action=AuditLog.Action.SALE_OVERRIDE, object_id=sale.pk).exists())

    def test_product_promotion_discount_is_applied_and_snapshotted(self):
        Promotion.objects.create(
            name="Cat food 20 off",
            discount_type=Promotion.DiscountType.PERCENTAGE,
            value=Decimal("20.00"),
            start_date=timezone.localdate() - timedelta(days=1),
            end_date=timezone.localdate() + timedelta(days=1),
            product=self.product,
            created_by=self.admin,
        )
        stock_batch = self.create_batch(actual_unit_cost=Decimal("1.50"), selling_price=Decimal("2.50"))

        sale = confirm_sale(
            cart_items=[{"stock_batch": stock_batch, "quantity": 1}],
            cashier=self.user,
        )

        item = sale.items.get()
        self.assertEqual(item.promotion_name_at_sale, "Cat food 20 off")
        self.assertEqual(item.original_unit_price, Decimal("2.50"))
        self.assertEqual(item.final_unit_price, Decimal("2.00"))
        self.assertEqual(item.discount_amount, Decimal("0.50"))
        self.assertEqual(sale.discount_amount, Decimal("0.50"))
        self.assertEqual(sale.final_amount, Decimal("2.00"))

    def test_below_cost_promotion_requires_explicit_allowance(self):
        promotion = Promotion.objects.create(
            name="Clearance final price",
            discount_type=Promotion.DiscountType.FIXED_FINAL_PRICE,
            value=Decimal("1.00"),
            start_date=timezone.localdate() - timedelta(days=1),
            end_date=timezone.localdate() + timedelta(days=1),
            product=self.product,
            allow_below_cost=False,
            created_by=self.admin,
        )
        stock_batch = self.create_batch(actual_unit_cost=Decimal("1.50"), selling_price=Decimal("2.50"))

        with self.assertRaisesMessage(ValidationError, "Manager approval required for this price."):
            confirm_sale(
                cart_items=[{"stock_batch": stock_batch, "quantity": 1}],
                cashier=self.user,
            )

        promotion.allow_below_cost = True
        promotion.save(update_fields=["allow_below_cost"])
        sale = confirm_sale(
            cart_items=[{"stock_batch": stock_batch, "quantity": 1}],
            cashier=self.user,
        )

        item = sale.items.get()
        self.assertIsNone(item.override_by)
        self.assertEqual(item.final_unit_price, Decimal("1.00"))
        self.assertTrue(AuditLog.objects.filter(action=AuditLog.Action.PROMOTION_BELOW_COST_SALE, object_id=sale.pk).exists())

    def test_best_valid_promotion_uses_lowest_price_without_stacking(self):
        Promotion.objects.create(
            name="Small category discount",
            discount_type=Promotion.DiscountType.PERCENTAGE,
            value=Decimal("10.00"),
            start_date=timezone.localdate() - timedelta(days=1),
            end_date=timezone.localdate() + timedelta(days=1),
            category=self.category,
            created_by=self.admin,
        )
        Promotion.objects.create(
            name="Product final price",
            discount_type=Promotion.DiscountType.FIXED_FINAL_PRICE,
            value=Decimal("1.75"),
            start_date=timezone.localdate() - timedelta(days=1),
            end_date=timezone.localdate() + timedelta(days=1),
            product=self.product,
            created_by=self.admin,
        )
        stock_batch = self.create_batch(actual_unit_cost=Decimal("1.50"), selling_price=Decimal("2.50"))

        sale = confirm_sale(
            cart_items=[{"stock_batch": stock_batch, "quantity": 1}],
            cashier=self.user,
        )

        item = sale.items.get()
        self.assertEqual(item.promotion_name_at_sale, "Product final price")
        self.assertEqual(item.final_unit_price, Decimal("1.75"))

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
                actual_unit_cost=Decimal("1.50"),
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


class PromotionDashboardTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_user(
            username="promotion-admin",
            password="Admin123",
            is_staff=True,
            is_superuser=True,
        )
        self.cashier = get_user_model().objects.create_user(username="promotion-cashier", password="Admin123")
        self.cashier.groups.add(Group.objects.get(name=CASHIER_GROUP))
        self.category = Category.objects.create(name="Food")
        self.product = Product.objects.create(
            product_code="P001",
            original_barcode="8851234567890",
            name="Cat Food",
            category=self.category,
            default_cost_price=Decimal("1.50"),
            default_selling_price=Decimal("2.50"),
        )

    def test_promotion_pages_are_admin_only(self):
        self.client.force_login(self.cashier)
        cashier_response = self.client.get(reverse("promotion-list"))

        self.client.force_login(self.admin)
        admin_response = self.client.get(reverse("promotion-list"))

        self.assertEqual(cashier_response.status_code, 403)
        self.assertContains(cashier_response, "Access denied", status_code=403)
        self.assertEqual(admin_response.status_code, 200)
        self.assertContains(admin_response, "Promotions")

    def test_admin_can_create_promotion_from_dashboard(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("promotion-create"),
            {
                "name": "Food discount",
                "discount_type": Promotion.DiscountType.FIXED_AMOUNT,
                "value": "0.50",
                "start_date": timezone.localdate().isoformat(),
                "end_date": (timezone.localdate() + timedelta(days=7)).isoformat(),
                "is_active": "on",
                "product": "",
                "category": self.category.id,
                "allow_below_cost": "",
            },
        )

        self.assertRedirects(response, reverse("promotion-list"))
        promotion = Promotion.objects.get(name="Food discount")
        self.assertEqual(promotion.created_by, self.admin)
        self.assertTrue(AuditLog.objects.filter(action=AuditLog.Action.PROMOTION_CREATE, object_id=promotion.pk).exists())

    def test_promotion_form_requires_product_or_category(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("promotion-create"),
            {
                "name": "No scope",
                "discount_type": Promotion.DiscountType.FIXED_AMOUNT,
                "value": "0.50",
                "start_date": timezone.localdate().isoformat(),
                "end_date": (timezone.localdate() + timedelta(days=7)).isoformat(),
                "is_active": "on",
                "product": "",
                "category": "",
                "allow_below_cost": "",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Promotion must apply to a product or category.")
        self.assertFalse(Promotion.objects.filter(name="No scope").exists())


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
                actual_unit_cost=Decimal("1.50"),
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
        # V5 Phase 5: every filtered list offers a consistent Filter + Reset.
        self.assertContains(history, "Filter")
        self.assertContains(history, "Reset")
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


class ReceiptTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_user(
            username="receipt-admin", password="Admin123", is_staff=True, is_superuser=True
        )
        self.cashier = get_user_model().objects.create_user(username="receipt-cashier", password="Admin123")
        self.cashier.groups.add(Group.objects.get_or_create(name=CASHIER_GROUP)[0])
        self.sale = Sale.objects.create(
            sale_no="S2606090001",
            cashier=self.cashier,
            total_amount=Decimal("2.50"),
            final_amount=Decimal("2.50"),
        )

    def test_receipt_uses_store_name_and_is_standalone(self):
        from core.models import StoreSetting

        setting = StoreSetting.load()
        setting.store_name = "Khlove Pet Store"
        setting.save()
        self.client.force_login(self.cashier)

        response = self.client.get(reverse("sale-receipt", kwargs={"sale_id": self.sale.id}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Khlove Pet Store")
        self.assertContains(response, "S2606090001")
        # Thermal receipt is standalone (no dashboard sidebar shell).
        self.assertNotContains(response, "app-sidebar")

    def test_admin_reprint_audits_and_redirects(self):
        self.client.force_login(self.admin)

        response = self.client.post(reverse("sale-reprint", kwargs={"sale_id": self.sale.id}))

        self.assertRedirects(
            response,
            f"{reverse('sale-receipt', kwargs={'sale_id': self.sale.id})}?print=1",
            fetch_redirect_response=False,
        )
        self.assertTrue(
            AuditLog.objects.filter(
                action=AuditLog.Action.RECEIPT_PRINT, object_id=str(self.sale.pk)
            ).exists()
        )

    def test_cashier_cannot_reprint(self):
        self.client.force_login(self.cashier)

        response = self.client.post(reverse("sale-reprint", kwargs={"sale_id": self.sale.id}))

        self.assertEqual(response.status_code, 403)
