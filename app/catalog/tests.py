from decimal import Decimal

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse

from audit.models import AuditLog
from core.permissions import ADMIN_GROUP, CASHIER_GROUP
from .admin import ProductAdmin
from .models import Brand, Category, Product, Supplier


class CatalogModelTests(TestCase):
    def test_product_original_barcode_is_unique_when_provided(self):
        category = Category.objects.create(name="Food")
        brand = Brand.objects.create(name="Melodu")

        Product.objects.create(
            product_code="P001",
            original_barcode="8851234567890",
            name="Cat Food",
            category=category,
            brand=brand,
            default_cost_price=Decimal("1.50"),
            default_selling_price=Decimal("2.50"),
        )

        with self.assertRaises(IntegrityError):
            Product.objects.create(
                product_code="P002",
                original_barcode="8851234567890",
                name="Dog Food",
                category=category,
                brand=brand,
                default_cost_price=Decimal("1.50"),
                default_selling_price=Decimal("2.50"),
            )

    def test_products_without_original_barcode_are_allowed(self):
        Product.objects.create(product_code="P001", name="Toy")
        Product.objects.create(product_code="P002", name="Collar")

        self.assertEqual(Product.objects.count(), 2)

    def test_inactive_product_status_is_available_in_admin_list_display(self):
        list_display = admin.site._registry[Product].list_display

        self.assertIn("is_active", list_display)

    def test_supplier_string_representation(self):
        supplier = Supplier.objects.create(name="Pet Wholesale")

        self.assertEqual(str(supplier), "Pet Wholesale")


class CatalogAdminTests(TestCase):
    def test_product_admin_search_and_filters_match_phase_1_requirements(self):
        product_admin = admin.site._registry[Product]

        self.assertIsInstance(product_admin, ProductAdmin)
        self.assertEqual(product_admin.search_fields, ("name", "product_code", "original_barcode"))
        self.assertEqual(product_admin.list_filter, ("is_active", "category", "brand"))


class ProductDashboardTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_user(username="catalog-admin", password="Admin123")
        admin_group, _created = Group.objects.get_or_create(name=ADMIN_GROUP)
        self.admin.groups.add(admin_group)
        self.cashier = get_user_model().objects.create_user(username="catalog-cashier", password="Admin123")
        cashier_group, _created = Group.objects.get_or_create(name=CASHIER_GROUP)
        self.cashier.groups.add(cashier_group)
        self.category = Category.objects.create(name="Food")
        self.brand = Brand.objects.create(name="Melodu")
        self.product = Product.objects.create(
            product_code="P001",
            original_barcode="8851234567890",
            name="Cat Food",
            category=self.category,
            brand=self.brand,
            default_cost_price=Decimal("1.50"),
            default_selling_price=Decimal("2.50"),
        )

    def test_product_list_renders_for_admin(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse("product-list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Product Catalog")
        self.assertContains(response, "Cat Food")
        self.assertContains(response, 'data-scan-target="#id_q"')

    def test_product_list_filters_by_search(self):
        Product.objects.create(product_code="P002", name="Dog Toy")
        self.client.force_login(self.admin)

        response = self.client.get(reverse("product-list"), {"q": "885123"})

        self.assertContains(response, "Cat Food")
        self.assertNotContains(response, "Dog Toy")

    def test_cashier_cannot_access_product_list(self):
        self.client.force_login(self.cashier)

        response = self.client.get(reverse("product-list"))

        self.assertEqual(response.status_code, 302)

    def test_admin_can_create_product_from_dashboard(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("product-create"),
            {
                "product_code": "P002",
                "original_barcode": "8850000000002",
                "name": "Dog Food",
                "category": self.category.id,
                "brand": self.brand.id,
                "unit": "Bag",
                "default_cost_price": "3.50",
                "default_selling_price": "5.50",
                "min_stock": "2",
                "description": "",
                "is_active": "on",
            },
        )

        self.assertRedirects(response, reverse("product-list"))
        self.assertTrue(Product.objects.filter(product_code="P002").exists())
        self.assertTrue(AuditLog.objects.filter(action=AuditLog.Action.CREATE, module="catalog").exists())

    def test_admin_can_edit_product_from_dashboard(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("product-edit", kwargs={"product_id": self.product.id}),
            {
                "product_code": "P001",
                "original_barcode": "8851234567890",
                "name": "Cat Food Updated",
                "category": self.category.id,
                "brand": self.brand.id,
                "unit": "Bag",
                "default_cost_price": "1.50",
                "default_selling_price": "2.75",
                "min_stock": "1",
                "description": "",
                "is_active": "on",
            },
        )

        self.assertRedirects(response, reverse("product-list"))
        self.product.refresh_from_db()
        self.assertEqual(self.product.name, "Cat Food Updated")
        self.assertTrue(AuditLog.objects.filter(action=AuditLog.Action.UPDATE, module="catalog").exists())
