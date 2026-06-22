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



def active_cart_items(session):
    state = session["pos_carts"]
    for cart in state["carts"]:
        if cart["id"] == state["active"]:
            return cart["items"]
    return []

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

    def create_batch(self, quantity=5, actual_unit_cost=Decimal("1.50"), selling_price=Decimal("2.50")):
        with TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            stock_batch, _movement = receive_stock(
                product=self.product,
                supplier=self.supplier,
                quantity=quantity,
                expiry_date=date(2027, 6, 1),
                actual_unit_cost=actual_unit_cost,
                selling_price=selling_price,
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

        response = self.client.post(
            reverse("pos-sale"), {"scan_value": self.product.original_barcode}, follow=True
        )

        # A product with exactly one sellable batch is added to the cart directly.
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, stock_batch.batch_no)
        self.assertEqual(
            active_cart_items(self.client.session),
            [{"stock_batch_id": stock_batch.id, "quantity": 1}],
        )

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
        self.assertEqual(active_cart_items(self.client.session)[0]["quantity"], 2)

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
        self.assertEqual(active_cart_items(self.client.session)[0]["quantity"], 3)

        self.client.post(reverse("pos-sale"), {"action": "remove_item", "stock_batch_id": stock_batch.id})
        self.assertEqual(active_cart_items(self.client.session), [])

    def test_cart_shows_promotion_price_explanation(self):
        stock_batch = self.create_batch()
        Promotion.objects.create(
            name="Cat food 20 off",
            discount_type=Promotion.DiscountType.PERCENTAGE,
            value=Decimal("20.00"),
            start_date=timezone.localdate() - timedelta(days=1),
            end_date=timezone.localdate() + timedelta(days=1),
            product=self.product,
            created_by=self.cashier,
        )
        self.client.force_login(self.cashier)
        self.client.post(
            reverse("pos-sale"),
            {"action": "add_batch", "stock_batch_id": stock_batch.id, "quantity": "1"},
        )

        response = self.client.get(reverse("pos-sale"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Promotion discount in cart")
        self.assertContains(response, "Cat food 20 off")
        self.assertContains(response, "Was")
        self.assertContains(response, "Now")
        self.assertContains(response, "Save")
        self.assertContains(response, "0.50")

    def test_cart_warns_cashier_when_manager_approval_is_needed(self):
        stock_batch = self.create_batch(actual_unit_cost=Decimal("1.50"), selling_price=Decimal("2.50"))
        Promotion.objects.create(
            name="Clearance final price",
            discount_type=Promotion.DiscountType.FIXED_FINAL_PRICE,
            value=Decimal("1.00"),
            start_date=timezone.localdate() - timedelta(days=1),
            end_date=timezone.localdate() + timedelta(days=1),
            product=self.product,
            allow_below_cost=False,
            created_by=self.cashier,
        )
        self.client.force_login(self.cashier)
        self.client.post(
            reverse("pos-sale"),
            {"action": "add_batch", "stock_batch_id": stock_batch.id, "quantity": "1"},
        )

        response = self.client.get(reverse("pos-sale"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Manager approval")
        self.assertContains(response, "need manager approval")


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
        self.assertContains(admin_response, "Promotion Labels")

    def test_promotion_list_shows_timeline_status(self):
        today = timezone.localdate()
        Promotion.objects.create(
            name="Running Promo",
            discount_type=Promotion.DiscountType.PERCENTAGE,
            value=Decimal("10.00"),
            start_date=today - timedelta(days=1),
            end_date=today + timedelta(days=1),
            is_active=True,
            category=self.category,
            created_by=self.admin,
        )
        Promotion.objects.create(
            name="Upcoming Promo",
            discount_type=Promotion.DiscountType.PERCENTAGE,
            value=Decimal("5.00"),
            start_date=today + timedelta(days=1),
            end_date=today + timedelta(days=7),
            is_active=True,
            category=self.category,
            created_by=self.admin,
        )
        Promotion.objects.create(
            name="Ended Promo",
            discount_type=Promotion.DiscountType.PERCENTAGE,
            value=Decimal("5.00"),
            start_date=today - timedelta(days=7),
            end_date=today - timedelta(days=1),
            is_active=True,
            category=self.category,
            created_by=self.admin,
        )
        Promotion.objects.create(
            name="Inactive Promo",
            discount_type=Promotion.DiscountType.PERCENTAGE,
            value=Decimal("5.00"),
            start_date=today - timedelta(days=1),
            end_date=today + timedelta(days=1),
            is_active=False,
            category=self.category,
            created_by=self.admin,
        )
        self.client.force_login(self.admin)

        response = self.client.get(reverse("promotion-list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Timeline")
        self.assertContains(response, "Promotions")
        self.assertContains(response, "Ends in")
        self.assertContains(response, "Starts in")
        self.assertContains(response, "Ended 1 day(s) ago")
        self.assertContains(response, "10% off")
        self.assertContains(response, "Running")
        self.assertContains(response, "Upcoming")
        self.assertContains(response, "Ended")
        self.assertContains(response, "Inactive")

    def test_promotion_form_renders_guidance_and_help(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse("promotion-create"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Promotions do not stack")
        self.assertContains(response, "Choose either a product or a category, not both.")
        self.assertContains(response, "Promotion Identity")
        self.assertContains(response, "Discount And Dates")
        self.assertContains(response, "Scope")
        self.assertContains(response, "Safety")
        self.assertContains(response, "Percentage, fixed amount off, or fixed final price.")
        self.assertContains(response, "Only allow this when the owner accepts selling below cost.")

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

    def test_promotion_form_rejects_product_and_category_together(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("promotion-create"),
            {
                "name": "Too broad",
                "discount_type": Promotion.DiscountType.FIXED_AMOUNT,
                "value": "0.50",
                "start_date": timezone.localdate().isoformat(),
                "end_date": (timezone.localdate() + timedelta(days=7)).isoformat(),
                "is_active": "on",
                "product": self.product.id,
                "category": self.category.id,
                "allow_below_cost": "",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Choose either a product or a category, not both.")
        self.assertFalse(Promotion.objects.filter(name="Too broad").exists())


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
        self.assertContains(history, "Sales Found")
        self.assertContains(history, "Receipt Reprints")
        self.assertContains(history, "Completed Revenue")
        self.assertEqual(detail.status_code, 200)
        self.assertContains(detail, "Cancel Sale")
        self.assertContains(detail, "Exception Tracking")

    def test_sales_history_filters_by_status_and_summarizes_exceptions(self):
        sale, _stock_batch = self.create_sale()
        cancel_sale(sale=sale, cancelled_by=self.admin, reason="Mistake")
        self.client.force_login(self.admin)

        response = self.client.get(reverse("sales-history"), {"status": Sale.Status.CANCELLED})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, sale.sale_no)
        self.assertContains(response, "Cancelled")
        self.assertEqual(response.context["summary"]["sale_count"], 1)
        self.assertEqual(response.context["summary"]["cancelled_count"], 1)

    def test_empty_sales_history_gives_filter_guidance(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse("sales-history"), {"payment_method": Sale.PaymentMethod.CASH})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No sales found.")
        self.assertContains(response, "Try different filters")

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

    def test_sale_detail_shows_receipt_reprint_tracking(self):
        AuditLog.objects.create(
            action=AuditLog.Action.RECEIPT_PRINT,
            module="pos",
            user=self.admin,
            object_type="Sale",
            object_id=str(self.sale.pk),
            object_display=self.sale.sale_no,
            new_value={"reprint": True},
        )
        self.client.force_login(self.admin)

        response = self.client.get(reverse("sale-detail", kwargs={"sale_id": self.sale.id}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Exception Tracking")
        self.assertContains(response, "Receipt Reprints")
        self.assertEqual(response.context["reprint_count"], 1)

    def test_cashier_cannot_reprint(self):
        self.client.force_login(self.cashier)

        response = self.client.post(reverse("sale-reprint", kwargs={"sale_id": self.sale.id}))

        self.assertEqual(response.status_code, 403)


class HeldSalesTests(TestCase):
    def setUp(self):
        self.cashier = get_user_model().objects.create_user(username="hold-cashier", password="Admin123")
        self.cashier.groups.add(Group.objects.get(name=CASHIER_GROUP))
        self.supplier = Supplier.objects.create(name="Pet Wholesale")
        self.product = Product.objects.create(
            product_code="P900",
            original_barcode="8859999999990",
            name="Hold Test Food",
            default_cost_price=Decimal("1.50"),
            default_selling_price=Decimal("2.50"),
        )
        self.client.force_login(self.cashier)

    def create_batch(self, **kwargs):
        from tempfile import TemporaryDirectory

        from django.test import override_settings
        from inventory.services import receive_stock

        with TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            stock_batch, _movement = receive_stock(
                product=self.product,
                supplier=self.supplier,
                quantity=kwargs.get("quantity", 10),
                expiry_date=date(2027, 6, 1),
                actual_unit_cost=Decimal("1.50"),
                selling_price=Decimal("2.50"),
                received_by=self.cashier,
            )
        return stock_batch

    def _add_to_cart(self, stock_batch, quantity=1):
        self.client.post(
            reverse("pos-sale"),
            {"action": "add_batch", "stock_batch_id": stock_batch.id, "quantity": str(quantity)},
        )

    def test_hold_parks_cart_and_starts_new_sale(self):
        stock_batch = self.create_batch()
        self._add_to_cart(stock_batch)

        response = self.client.post(reverse("pos-sale"), {"action": "hold"}, follow=True)

        self.assertEqual(response.status_code, 200)
        state = self.client.session["pos_carts"]
        self.assertEqual(len(state["carts"]), 2)
        self.assertEqual(active_cart_items(self.client.session), [])
        held = [cart for cart in state["carts"] if cart["id"] != state["active"]][0]
        self.assertEqual(held["items"][0]["stock_batch_id"], stock_batch.id)
        self.assertContains(response, "Held 1")

    def test_resume_switches_back_to_held_sale(self):
        stock_batch = self.create_batch()
        self._add_to_cart(stock_batch)
        self.client.post(reverse("pos-sale"), {"action": "hold"})
        held_id = self.client.session["pos_carts"]["carts"][0]["id"]

        self.client.post(reverse("pos-sale"), {"action": "resume", "cart_id": held_id})

        self.assertEqual(self.client.session["pos_carts"]["active"], held_id)
        self.assertEqual(active_cart_items(self.client.session)[0]["stock_batch_id"], stock_batch.id)

    def test_hold_empty_cart_is_rejected(self):
        response = self.client.post(reverse("pos-sale"), {"action": "hold"}, follow=True)
        self.assertContains(response, "nothing to hold")
        self.assertEqual(len(self.client.session["pos_carts"]["carts"]), 1)

    def test_hold_limit_is_ten_open_sales(self):
        stock_batch = self.create_batch(quantity=50)
        for _ in range(9):
            self._add_to_cart(stock_batch)
            self.client.post(reverse("pos-sale"), {"action": "hold"})
        self.assertEqual(len(self.client.session["pos_carts"]["carts"]), 10)

        self._add_to_cart(stock_batch)
        response = self.client.post(reverse("pos-sale"), {"action": "hold"}, follow=True)

        self.assertContains(response, "Limit of 10 open sales")
        self.assertEqual(len(self.client.session["pos_carts"]["carts"]), 10)

    def test_legacy_single_cart_session_is_migrated(self):
        stock_batch = self.create_batch()
        session = self.client.session
        session["pos_cart"] = [{"stock_batch_id": stock_batch.id, "quantity": 2}]
        session.save()

        response = self.client.get(reverse("pos-sale"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(active_cart_items(self.client.session)[0]["quantity"], 2)
        self.assertNotIn("pos_cart", self.client.session)


class QuickKeyTests(TestCase):
    def setUp(self):
        self.cashier = get_user_model().objects.create_user(username="qk-cashier", password="Admin123")
        self.cashier.groups.add(Group.objects.get(name=CASHIER_GROUP))
        self.supplier = Supplier.objects.create(name="Pet Wholesale")
        self.product = Product.objects.create(
            product_code="P910",
            original_barcode="8851111111119",
            name="Quick Cat Food",
            default_cost_price=Decimal("1.50"),
            default_selling_price=Decimal("2.50"),
        )
        self.client.force_login(self.cashier)

    def test_hand_picked_quick_keys_render(self):
        from core.models import StoreSetting

        StoreSetting.load().quick_key_products.add(self.product)

        response = self.client.get(reverse("pos-sale"))

        self.assertContains(response, "Quick Keys")
        self.assertContains(response, "Quick Cat Food")
        self.assertContains(response, 'value="8851111111119"')
        self.assertNotContains(response, 'value="P910"')

    def test_quick_key_products_without_barcode_are_hidden(self):
        from core.models import StoreSetting

        no_barcode = Product.objects.create(
            product_code="P911",
            name="No Barcode Product",
            default_cost_price=Decimal("1.50"),
            default_selling_price=Decimal("2.50"),
        )
        StoreSetting.load().quick_key_products.add(no_barcode)

        response = self.client.get(reverse("pos-sale"))

        self.assertNotContains(response, "Quick Keys")
        self.assertNotContains(response, "No Barcode Product")

    def test_no_quick_keys_section_when_nothing_configured_or_sold(self):
        response = self.client.get(reverse("pos-sale"))
        self.assertNotContains(response, "Quick Keys")

    def test_active_product_promotion_renders_as_promo_key(self):
        from django.utils import timezone

        Promotion.objects.create(
            name="Cat food deal",
            discount_type=Promotion.DiscountType.PERCENTAGE,
            value=Decimal("10.00"),
            start_date=timezone.localdate(),
            end_date=timezone.localdate(),
            is_active=True,
            product=self.product,
            created_by=self.cashier,
        )

        response = self.client.get(reverse("pos-sale"))

        self.assertContains(response, "Promotions")
        self.assertContains(response, "-10%")
        self.assertContains(response, 'value="8851111111119"')


class PaymentFlowTests(TestCase):
    def setUp(self):
        self.cashier = get_user_model().objects.create_user(username="pay-cashier", password="Admin123")
        self.cashier.groups.add(Group.objects.get(name=CASHIER_GROUP))
        self.supplier = Supplier.objects.create(name="Pet Wholesale")
        self.product = Product.objects.create(
            product_code="P920",
            original_barcode="8852222222229",
            name="Pay Test Food",
            default_cost_price=Decimal("1.50"),
            default_selling_price=Decimal("2.50"),
        )
        self.client.force_login(self.cashier)

    def create_batch(self):
        from tempfile import TemporaryDirectory

        from django.test import override_settings
        from inventory.services import receive_stock

        with TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            stock_batch, _movement = receive_stock(
                product=self.product,
                supplier=self.supplier,
                quantity=10,
                expiry_date=date(2027, 6, 1),
                actual_unit_cost=Decimal("1.50"),
                selling_price=Decimal("2.50"),
                received_by=self.cashier,
            )
        return stock_batch

    def _checkout(self, **extra):
        stock_batch = self.create_batch()
        self.client.post(
            reverse("pos-sale"),
            {"action": "add_batch", "stock_batch_id": stock_batch.id, "quantity": "2"},
        )
        data = {"action": "confirm", "payment_method": "CASH", "discount_amount": "0"}
        data.update(extra)
        return self.client.post(reverse("pos-sale"), data, follow=True)

    def test_cash_sale_persists_received_and_change(self):
        response = self._checkout(amount_received="10.00")
        self.assertEqual(response.status_code, 200)
        sale = Sale.objects.latest("id")
        self.assertEqual(sale.amount_received, Decimal("10.00"))
        self.assertEqual(sale.change_due, Decimal("5.00"))

    def test_cash_sale_rejects_insufficient_amount(self):
        response = self._checkout(amount_received="1.00")
        self.assertContains(response, "less than the total due")
        self.assertEqual(Sale.objects.count(), 0)

    def test_khqr_sale_ignores_received_amount(self):
        response = self._checkout(payment_method="KHQR", amount_received="10.00")
        self.assertEqual(response.status_code, 200)
        sale = Sale.objects.latest("id")
        self.assertEqual(sale.payment_method, "KHQR")
        self.assertIsNone(sale.amount_received)
        self.assertIsNone(sale.change_due)

    def test_receipt_shows_change_and_khr(self):
        self._checkout(amount_received="10.00")
        sale = Sale.objects.latest("id")
        response = self.client.get(reverse("sale-receipt", kwargs={"sale_id": sale.id}))
        self.assertContains(response, "Received")
        self.assertContains(response, "10.00")
        self.assertContains(response, "៛")
        self.assertContains(response, "20,500")
