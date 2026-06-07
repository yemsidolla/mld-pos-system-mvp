from decimal import Decimal

from django.contrib import admin
from django.db import IntegrityError
from django.test import TestCase

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
