from datetime import date
from decimal import Decimal
from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import StaffProfile
from audit.models import AuditLog
from catalog.models import Category, Product, Supplier
from core.permissions import ROLE_INVENTORY, ROLE_VIEWER
from inventory.models import StockBatch
from inventory.services import receive_stock
from pos.models import Promotion

from .models import LabelTemplate


def _profile_user(username, role):
    user = get_user_model().objects.create_user(username=username, password="Admin123")
    StaffProfile.objects.create(user=user, role=role)
    return user


class LabelTemplateModelTests(TestCase):
    def test_default_template_is_unique_per_type(self):
        first = LabelTemplate.objects.create(name="A", template_type="PRODUCT", is_default=True)
        second = LabelTemplate.objects.create(name="B", template_type="PRODUCT", is_default=True)
        first.refresh_from_db()
        self.assertFalse(first.is_default)
        self.assertTrue(second.is_default)

    def test_default_migration_seeds_a_product_template(self):
        # The data migration creates a default product template.
        self.assertTrue(LabelTemplate.objects.filter(template_type="PRODUCT", is_default=True).exists())
        self.assertEqual(LabelTemplate.default_for("PRODUCT").name, "Standard Product Label")


class LabelTemplateAccessTests(TestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user(
            username="owner", password="Admin123", is_staff=True, is_superuser=True
        )

    def test_owner_can_manage_templates(self):
        self.client.force_login(self.owner)
        self.assertEqual(self.client.get(reverse("label-template-list")).status_code, 200)

        response = self.client.post(
            reverse("label-template-create"),
            {
                "name": "Shelf Tag",
                "template_type": "SHELF",
                "paper_width_mm": "60",
                "paper_height_mm": "40",
                "orientation": "LANDSCAPE",
                "font_size_px": "12",
                "show_store_name": "on",
                "show_product_name": "on",
                "show_price": "on",
                "header_text": "",
                "custom_footer": "",
            },
        )
        self.assertRedirects(response, reverse("label-template-list"))
        self.assertTrue(LabelTemplate.objects.filter(name="Shelf Tag").exists())
        self.assertTrue(
            AuditLog.objects.filter(action=AuditLog.Action.CREATE, module="labels").exists()
        )

    def test_inventory_staff_cannot_manage_templates(self):
        self.client.force_login(_profile_user("inv", ROLE_INVENTORY))
        self.assertEqual(self.client.get(reverse("label-template-list")).status_code, 403)

    def test_viewer_cannot_open_label_print(self):
        self.client.force_login(_profile_user("vw", ROLE_VIEWER))
        self.assertEqual(self.client.get(reverse("label-print")).status_code, 403)


class LabelPrintTests(TestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user(
            username="print-owner", password="Admin123", is_staff=True, is_superuser=True
        )
        self.supplier = Supplier.objects.create(name="Pet Wholesale")
        self.product = Product.objects.create(
            product_code="P001",
            original_barcode="8851234567890",
            name="Cat Food",
            default_cost_price=Decimal("1.50"),
            default_selling_price=Decimal("2.50"),
        )

    def _batch(self):
        with TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            batch, _ = receive_stock(
                product=self.product,
                supplier=self.supplier,
                quantity=10,
                expiry_date=date(2027, 6, 1),
                actual_unit_cost=Decimal("1.50"),
                selling_price=Decimal("2.50"),
                received_by=self.owner,
            )
        return StockBatch.objects.get(pk=batch.pk)

    def test_inventory_staff_can_open_print_page(self):
        self.client.force_login(_profile_user("inv2", ROLE_INVENTORY))
        self.assertEqual(self.client.get(reverse("label-print")).status_code, 200)

    def test_batch_query_param_preselects_batch_and_template(self):
        batch = self._batch()
        self.client.force_login(self.owner)

        response = self.client.get(reverse("label-print"), {"batch": batch.id})

        self.assertEqual(response.status_code, 200)
        initial = response.context["form"].initial
        self.assertEqual(initial.get("stock_batches"), [batch.pk])
        # The default PRODUCT template is pre-selected for a one-click flow.
        self.assertEqual(initial.get("template"), LabelTemplate.default_for("PRODUCT").pk)

    def test_print_renders_labels_and_audits(self):
        batch = self._batch()
        template = LabelTemplate.default_for("PRODUCT")
        self.client.force_login(self.owner)

        response = self.client.post(
            reverse("label-print"),
            {
                "template": template.id,
                "stock_batches": [batch.id],
                "quantity": "3",
                "action": "print",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cat Food")
        # quantity 3 for one batch => three rendered label cards.
        self.assertContains(response, 'class="tpl-label"', count=3)
        self.assertTrue(
            AuditLog.objects.filter(
                action=AuditLog.Action.BARCODE_PRINT, module="labels"
            ).exists()
        )


class PromotionLabelTests(TestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user(
            username="promo-owner", password="Admin123", is_staff=True, is_superuser=True
        )
        self.category = Category.objects.create(name="Food")
        self.product = Product.objects.create(
            product_code="P001",
            name="Cat Food",
            category=self.category,
            default_selling_price=Decimal("10.00"),
        )
        self.promotion = Promotion.objects.create(
            name="Cat Week",
            discount_type=Promotion.DiscountType.PERCENTAGE,
            value=Decimal("20.00"),
            start_date=date(2026, 6, 1),
            end_date=date(2026, 12, 31),
            is_active=True,
            category=self.category,
            created_by=self.owner,
        )

    def test_promotion_label_print_renders_old_and_new_price(self):
        template = LabelTemplate.default_for("PROMOTION")
        self.assertIsNotNone(template)
        self.client.force_login(self.owner)

        response = self.client.post(
            reverse("promotion-label-print"),
            {
                "promotion": self.promotion.id,
                "template": template.id,
                "quantity": "2",
                "custom_text": "Special Offer",
                "action": "print",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cat Food")
        self.assertContains(response, "10.00")  # original price
        self.assertContains(response, "8.00")   # 20% off
        self.assertContains(response, 'class="promo-label"', count=2)
        self.assertTrue(
            AuditLog.objects.filter(
                action=AuditLog.Action.BARCODE_PRINT, module="labels", object_id=str(self.promotion.pk)
            ).exists()
        )

    def test_inventory_staff_can_open_but_viewer_cannot(self):
        self.client.force_login(_profile_user("promo-inv", ROLE_INVENTORY))
        self.assertEqual(self.client.get(reverse("promotion-label-print")).status_code, 200)

        self.client.force_login(_profile_user("promo-vw", ROLE_VIEWER))
        self.assertEqual(self.client.get(reverse("promotion-label-print")).status_code, 403)
