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
from .models import Brand, Category, Product, ProductTag, Supplier, SupplierProductCost


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

    def test_supplier_product_cost_is_unique_per_product_supplier(self):
        supplier = Supplier.objects.create(name="Pet Wholesale")
        product = Product.objects.create(product_code="P001", name="Cat Food")
        SupplierProductCost.objects.create(
            product=product,
            supplier=supplier,
            reference_unit_cost=Decimal("1.50"),
        )

        with self.assertRaises(IntegrityError):
            SupplierProductCost.objects.create(
                product=product,
                supplier=supplier,
                reference_unit_cost=Decimal("1.75"),
            )


class CatalogAdminTests(TestCase):
    def test_product_admin_search_and_filters_match_phase_1_requirements(self):
        product_admin = admin.site._registry[Product]

        self.assertIsInstance(product_admin, ProductAdmin)
        self.assertEqual(product_admin.search_fields, ("name", "product_code", "original_barcode"))
        self.assertEqual(
            product_admin.list_filter,
            ("is_active", "category", "brand", "animal_type", "life_stage", "tags"),
        )


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

    def test_product_list_paginates(self):
        for index in range(30):
            Product.objects.create(product_code=f"PG{index:03d}", name=f"Bulk Product {index}")
        self.client.force_login(self.admin)

        first = self.client.get(reverse("product-list"))
        second = self.client.get(reverse("product-list"), {"page": 2})

        # 31 products total (1 from setUp + 30) across pages of 25.
        self.assertEqual(first.context["page_obj"].paginator.num_pages, 2)
        self.assertEqual(first.context["product_count"], 31)
        self.assertEqual(len(first.context["page_obj"].object_list), 25)
        self.assertEqual(len(second.context["page_obj"].object_list), 6)

    def test_cashier_cannot_access_product_list(self):
        self.client.force_login(self.cashier)

        response = self.client.get(reverse("product-list"))

        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "Access denied", status_code=403)

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

    def test_product_form_renders_quick_add_controls(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse("product-create"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-quick-create-type="category"')
        self.assertContains(response, 'data-quick-create-target="#id_category"')
        self.assertContains(response, 'data-quick-create-type="brand"')
        self.assertContains(response, 'data-quick-create-target="#id_brand"')


class CatalogQuickCreateTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_user(username="quick-admin", password="Admin123")
        admin_group, _created = Group.objects.get_or_create(name=ADMIN_GROUP)
        self.admin.groups.add(admin_group)
        self.cashier = get_user_model().objects.create_user(username="quick-cashier", password="Admin123")
        cashier_group, _created = Group.objects.get_or_create(name=CASHIER_GROUP)
        self.cashier.groups.add(cashier_group)

    def test_admin_can_quick_create_category(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("catalog-quick-create"),
            {"type": "category", "name": "Treats", "description": "Snack products"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["item"]["type"], "category")
        self.assertEqual(payload["item"]["label"], "Treats")
        self.assertTrue(Category.objects.filter(name="Treats", is_active=True).exists())
        self.assertTrue(AuditLog.objects.filter(action=AuditLog.Action.CREATE, object_type="Category").exists())

    def test_admin_can_quick_create_brand(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("catalog-quick-create"),
            {"type": "brand", "name": "Happy Paw", "description": ""},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(Brand.objects.filter(name="Happy Paw", is_active=True).exists())
        self.assertTrue(AuditLog.objects.filter(action=AuditLog.Action.CREATE, object_type="Brand").exists())

    def test_admin_can_quick_create_supplier(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("catalog-quick-create"),
            {
                "type": "supplier",
                "name": "Pet Wholesale",
                "contact_person": "Sophea",
                "phone": "012345678",
                "telegram": "@supplier",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(Supplier.objects.filter(name="Pet Wholesale", is_active=True).exists())
        self.assertTrue(AuditLog.objects.filter(action=AuditLog.Action.CREATE, object_type="Supplier").exists())

    def test_quick_create_rejects_case_insensitive_duplicate_name(self):
        Category.objects.create(name="Treats")
        self.client.force_login(self.admin)

        response = self.client.post(reverse("catalog-quick-create"), {"type": "category", "name": "treats"})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Category.objects.count(), 1)
        self.assertIn("name", response.json()["errors"])

    def test_quick_create_rejects_unsupported_type(self):
        self.client.force_login(self.admin)

        response = self.client.post(reverse("catalog-quick-create"), {"type": "product", "name": "Toy"})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["status"], "error")

    def test_cashier_cannot_quick_create_master_data(self):
        self.client.force_login(self.cashier)

        response = self.client.post(reverse("catalog-quick-create"), {"type": "category", "name": "Treats"})

        self.assertEqual(response.status_code, 403)
        self.assertFalse(Category.objects.filter(name="Treats").exists())

    def test_anonymous_user_is_redirected_from_quick_create(self):
        response = self.client.post(reverse("catalog-quick-create"), {"type": "category", "name": "Treats"})

        self.assertEqual(response.status_code, 302)
        self.assertFalse(Category.objects.filter(name="Treats").exists())


class MasterDataDashboardTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_user(username="master-admin", password="Admin123")
        admin_group, _created = Group.objects.get_or_create(name=ADMIN_GROUP)
        self.admin.groups.add(admin_group)
        self.cashier = get_user_model().objects.create_user(username="master-cashier", password="Admin123")
        cashier_group, _created = Group.objects.get_or_create(name=CASHIER_GROUP)
        self.cashier.groups.add(cashier_group)

    def test_admin_dashboard_links_to_master_data_pages(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse("dashboard-home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("category-list"))
        self.assertContains(response, reverse("brand-list"))
        self.assertContains(response, reverse("supplier-list"))
        self.assertContains(response, reverse("supplier-product-cost-list"))
        self.assertContains(response, reverse("promotion-list"))

    def test_admin_can_create_category_from_dashboard(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("category-create"),
            {
                "name": "Treats",
                "description": "Snack products",
                "is_active": "on",
            },
        )

        self.assertRedirects(response, reverse("category-list"))
        self.assertTrue(Category.objects.filter(name="Treats").exists())
        self.assertTrue(AuditLog.objects.filter(action=AuditLog.Action.CREATE, object_type="Category").exists())

    def test_admin_can_create_brand_from_dashboard(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("brand-create"),
            {
                "name": "Happy Paw",
                "description": "",
                "is_active": "on",
            },
        )

        self.assertRedirects(response, reverse("brand-list"))
        self.assertTrue(Brand.objects.filter(name="Happy Paw").exists())

    def test_admin_can_edit_supplier_from_dashboard(self):
        supplier = Supplier.objects.create(name="Pet Wholesale", phone="010000000")
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("supplier-edit", kwargs={"supplier_id": supplier.id}),
            {
                "name": "Pet Wholesale",
                "contact_person": "Sophea",
                "phone": "012345678",
                "telegram": "@supplier",
                "address": "Phnom Penh",
                "notes": "",
                "is_active": "on",
            },
        )

        self.assertRedirects(response, reverse("supplier-list"))
        supplier.refresh_from_db()
        self.assertEqual(supplier.contact_person, "Sophea")
        self.assertEqual(supplier.phone, "012345678")
        self.assertTrue(AuditLog.objects.filter(action=AuditLog.Action.UPDATE, object_type="Supplier").exists())

    def test_admin_can_create_supplier_product_cost_from_dashboard(self):
        category = Category.objects.create(name="Food")
        product = Product.objects.create(product_code="P001", name="Cat Food", category=category)
        supplier = Supplier.objects.create(name="Pet Wholesale")
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("supplier-product-cost-create"),
            {
                "product": product.id,
                "supplier": supplier.id,
                "reference_unit_cost": "1.75",
                "notes": "Vendor June quote",
                "is_active": "on",
            },
        )

        self.assertRedirects(response, reverse("supplier-product-cost-list"))
        cost = SupplierProductCost.objects.get(product=product, supplier=supplier)
        self.assertEqual(cost.reference_unit_cost, Decimal("1.75"))
        self.assertTrue(AuditLog.objects.filter(action=AuditLog.Action.COST_CHANGE, object_type="SupplierProductCost").exists())

    def test_cashier_cannot_access_supplier_product_cost_pages(self):
        self.client.force_login(self.cashier)

        response = self.client.get(reverse("supplier-product-cost-list"))

        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "Access denied", status_code=403)

    def test_cashier_cannot_access_master_data_pages(self):
        self.client.force_login(self.cashier)

        response = self.client.get(reverse("category-list"))

        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "Access denied", status_code=403)


class ProductClassificationTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_user(username="class-admin", password="Admin123")
        self.admin.groups.add(Group.objects.get_or_create(name=ADMIN_GROUP)[0])
        self.category = Category.objects.create(name="Food")
        self.brand = Brand.objects.create(name="Melodu")

    def _base_payload(self, **overrides):
        payload = {
            "product_code": "P010",
            "original_barcode": "8850000000010",
            "name": "Kitten Food",
            "category": self.category.id,
            "brand": self.brand.id,
            "unit": "Bag",
            "default_cost_price": "1.50",
            "default_selling_price": "2.50",
            "min_stock": "1",
            "description": "",
            "is_active": "on",
        }
        payload.update(overrides)
        return payload

    def test_product_can_have_classification_and_tags(self):
        product = Product.objects.create(product_code="P001", name="Cat Food")
        tag = ProductTag.objects.create(name="Grain Free")
        product.animal_type = Product.AnimalType.CAT
        product.life_stage = Product.LifeStage.ADULT
        product.save()
        product.tags.add(tag)

        product.refresh_from_db()
        self.assertEqual(product.animal_type, "CAT")
        self.assertEqual(product.life_stage, "ADULT")
        self.assertEqual(list(product.tags.values_list("name", flat=True)), ["Grain Free"])

    def test_existing_product_without_classification_is_valid(self):
        product = Product.objects.create(product_code="P002", name="Plain Product")
        self.assertEqual(product.animal_type, "")
        self.assertEqual(product.life_stage, "")
        self.assertEqual(product.tags.count(), 0)

    def test_create_product_with_classification_and_tags_via_dashboard(self):
        tag1 = ProductTag.objects.create(name="Grain Free")
        tag2 = ProductTag.objects.create(name="Indoor")
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("product-create"),
            self._base_payload(animal_type="CAT", life_stage="KITTEN", tags=[tag1.id, tag2.id]),
        )

        self.assertRedirects(response, reverse("product-list"))
        product = Product.objects.get(product_code="P010")
        self.assertEqual(product.animal_type, "CAT")
        self.assertEqual(product.life_stage, "KITTEN")
        self.assertEqual(set(product.tags.values_list("name", flat=True)), {"Grain Free", "Indoor"})
        audit = AuditLog.objects.filter(action=AuditLog.Action.CREATE, module="catalog").latest("created_at")
        self.assertEqual(audit.new_value.get("tags"), ["Grain Free", "Indoor"])

    def test_product_list_filters_by_animal_type_and_tag(self):
        dental = ProductTag.objects.create(name="Dental Care")
        cat_food = Product.objects.create(
            product_code="C1", name="Cat Food", animal_type=Product.AnimalType.CAT
        )
        cat_food.tags.add(dental)
        Product.objects.create(product_code="D1", name="Dog Food", animal_type=Product.AnimalType.DOG)
        self.client.force_login(self.admin)

        by_animal = self.client.get(reverse("product-list"), {"animal_type": "CAT"})
        self.assertContains(by_animal, "Cat Food")
        self.assertNotContains(by_animal, "Dog Food")

        by_tag = self.client.get(reverse("product-list"), {"tag": dental.id})
        self.assertContains(by_tag, "Cat Food")
        self.assertNotContains(by_tag, "Dog Food")

    def test_product_form_renders_classification_fields(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse("product-create"))

        self.assertContains(response, 'name="animal_type"')
        self.assertContains(response, 'name="life_stage"')
        self.assertContains(response, 'name="tags"')
