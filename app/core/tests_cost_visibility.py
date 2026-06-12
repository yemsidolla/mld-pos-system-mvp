"""Role-based cost visibility (configurable in Store Settings)."""
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import StaffProfile
from catalog.models import Product, Supplier
from core.models import StoreSetting
from core.permissions import ROLE_INVENTORY, ROLE_MANAGER, ROLE_VIEWER, can_view_costs
from inventory.models import StockBatch
from pos.models import Sale

User = get_user_model()


def make_user(username, role):
    user = User.objects.create_user(username=username, password="x")
    StaffProfile.objects.create(user=user, role=role)
    return user


def set_cost_roles(roles):
    setting = StoreSetting.load()
    setting.cost_visible_roles = roles
    setting.save()


class CostVisibilityCapabilityTests(TestCase):
    def test_default_preserves_v5_visibility(self):
        self.assertTrue(can_view_costs(make_user("m", ROLE_MANAGER)))
        self.assertTrue(can_view_costs(make_user("i", ROLE_INVENTORY)))
        self.assertTrue(can_view_costs(make_user("v", ROLE_VIEWER)))

    def test_owner_always_sees_costs_even_with_empty_list(self):
        set_cost_roles([])
        owner = User.objects.create_superuser("boss", "b@x.com", "x")
        self.assertTrue(can_view_costs(owner))

    def test_removed_role_loses_cost_visibility(self):
        user = make_user("m", ROLE_MANAGER)
        set_cost_roles(["INVENTORY"])
        self.assertFalse(can_view_costs(user))


class CostVisibilityPageTests(TestCase):
    def setUp(self):
        self.supplier = Supplier.objects.create(name="Pet Wholesale")
        self.product = Product.objects.create(
            product_code="P001",
            original_barcode="8851234567890",
            name="Cat Food",
            min_stock=1,
            default_selling_price=Decimal("9.99"),
        )
        self.receiver = User.objects.create_user(username="receiver", password="x")
        self.batch = StockBatch.objects.create(
            product=self.product,
            supplier=self.supplier,
            batch_no="B0001",
            custom_code="8851234567890-B0001-991231",
            expiry_date=timezone.localdate() + timedelta(days=365),
            quantity_received=10,
            quantity_available=10,
            actual_unit_cost=Decimal("4.44"),
            selling_price=Decimal("9.99"),
            received_by=self.receiver,
        )

    def test_inventory_user_sees_costs_by_default(self):
        self.client.force_login(make_user("stock", ROLE_INVENTORY))
        response = self.client.get(reverse("stock-batch-detail", kwargs={"batch_id": self.batch.id}))
        self.assertContains(response, "4.44")

    def test_inventory_user_costs_hidden_when_role_removed(self):
        set_cost_roles(["MANAGER"])
        self.client.force_login(make_user("stock", ROLE_INVENTORY))
        response = self.client.get(reverse("stock-batch-detail", kwargs={"batch_id": self.batch.id}))
        self.assertNotContains(response, "4.44")
        self.assertContains(response, "Hidden")

    def test_reference_costs_blocked_without_visibility(self):
        set_cost_roles(["INVENTORY"])
        self.client.force_login(make_user("mgr", ROLE_MANAGER))
        response = self.client.get(reverse("supplier-product-cost-list"))
        self.assertEqual(response.status_code, 403)

    def test_reference_costs_open_for_owner_even_with_empty_list(self):
        set_cost_roles([])
        self.client.force_login(User.objects.create_superuser("boss", "b@x.com", "x"))
        response = self.client.get(reverse("supplier-product-cost-list"))
        self.assertEqual(response.status_code, 200)

    def test_sale_detail_cost_column_follows_setting(self):
        sale = Sale.objects.create(
            sale_no="S-0001",
            cashier=make_user("till", ROLE_VIEWER),
            total_amount=Decimal("9.99"),
            discount_amount=Decimal("0.00"),
            final_amount=Decimal("9.99"),
            payment_method=Sale.PaymentMethod.CASH,
            status=Sale.Status.COMPLETED,
        )
        viewer = make_user("audit", ROLE_VIEWER)
        self.client.force_login(viewer)

        response = self.client.get(reverse("sale-detail", kwargs={"sale_id": sale.id}))
        self.assertContains(response, "Cost Basis")

        set_cost_roles(["MANAGER"])
        response = self.client.get(reverse("sale-detail", kwargs={"sale_id": sale.id}))
        self.assertNotContains(response, "Cost Basis")


class CostVisibilitySettingsFormTests(TestCase):
    def test_owner_can_update_visible_roles(self):
        self.client.force_login(User.objects.create_superuser("boss", "b@x.com", "x"))
        setting = StoreSetting.load()
        response = self.client.post(
            reverse("store-settings"),
            {
                "store_name": setting.store_name,
                "address": "",
                "phone": "",
                "receipt_header": "",
                "receipt_footer": setting.receipt_footer,
                "receipt_paper_width_mm": setting.receipt_paper_width_mm,
                "receipt_font_size_px": setting.receipt_font_size_px,
                "currency_symbol": setting.currency_symbol,
                "cost_visible_roles": ["MANAGER"],
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(StoreSetting.load().cost_visible_roles, ["MANAGER"])
