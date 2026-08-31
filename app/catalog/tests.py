from io import BytesIO
from decimal import Decimal
from tempfile import TemporaryDirectory

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.html import escape
from PIL import Image

from audit.models import AuditLog
from core.permissions import ADMIN_GROUP, CASHIER_GROUP
from .admin import ProductAdmin
from .models import AnimalTypeOption, Brand, Category, Product, ProductTag, Supplier, SupplierProductCost


def tiny_image_upload(name="cat.png"):
    buffer = BytesIO()
    Image.new("RGB", (1, 1), color="white").save(buffer, format="PNG")
    return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/png")


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
            ("is_active", "category", "brand", "animal_types", "life_stage", "tags"),
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
        self.assertContains(response, 'type="search" name="q"')
        self.assertContains(response, "Search name, code, barcode, or tag")
        self.assertContains(response, "Photo")
        self.assertContains(response, "product-thumb-empty")

    def test_product_list_renders_product_image_when_available(self):
        self.client.force_login(self.admin)

        with TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            self.product.image = tiny_image_upload()
            self.product.save()

            response = self.client.get(reverse("product-list"))

            self.assertEqual(response.status_code, 200)
            # Hook class kept alongside Tailwind utilities (same pattern as base.html).
            self.assertContains(response, "product-thumb")
            self.assertContains(response, escape(self.product.image.url))
            self.assertNotContains(response, "product-thumb-empty")

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
        self.assertContains(response, 'data-quick-create-type="animal_type"')
        self.assertContains(response, 'data-quick-create-target="#id_animal_types"')
        self.assertContains(response, 'data-quick-create-field-name="animal_types"')


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

    def test_admin_can_quick_create_animal_type(self):
        self.client.force_login(self.admin)

        response = self.client.post(reverse("catalog-quick-create"), {"type": "animal_type", "name": "Reptile"})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["item"]["type"], "animal_type")
        animal_type = AnimalTypeOption.objects.get(name="Reptile")
        self.assertEqual(animal_type.code, "REPTILE")
        self.assertTrue(animal_type.is_active)
        self.assertTrue(AuditLog.objects.filter(action=AuditLog.Action.CREATE, object_type="AnimalTypeOption").exists())

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
        self.assertContains(response, reverse("animal-type-list"))
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

    def test_admin_can_create_animal_type_from_dashboard(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("animal-type-create"),
            {
                "name": "Reptile",
                "code": "",
                "is_active": "on",
            },
        )

        self.assertRedirects(response, reverse("animal-type-list"))
        animal_type = AnimalTypeOption.objects.get(name="Reptile")
        self.assertEqual(animal_type.code, "REPTILE")
        self.assertTrue(AuditLog.objects.filter(action=AuditLog.Action.CREATE, object_type="AnimalTypeOption").exists())

    def test_admin_can_edit_animal_type_from_dashboard(self):
        animal_type = AnimalTypeOption.objects.create(name="Reptile", code="REPTILE")
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("animal-type-edit", kwargs={"animal_type_id": animal_type.id}),
            {
                "name": "Reptiles",
                "code": "REPTILE",
                "is_active": "on",
            },
        )

        self.assertRedirects(response, reverse("animal-type-list"))
        animal_type.refresh_from_db()
        self.assertEqual(animal_type.name, "Reptiles")
        self.assertTrue(AuditLog.objects.filter(action=AuditLog.Action.UPDATE, object_type="AnimalTypeOption").exists())

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

    def test_reference_cost_pages_explain_cost_terms(self):
        category = Category.objects.create(name="Food")
        product = Product.objects.create(
            product_code="P002",
            name="Kitten Food",
            category=category,
            default_cost_price=Decimal("1.25"),
        )
        supplier = Supplier.objects.create(name="Pet Wholesale")
        SupplierProductCost.objects.create(
            product=product,
            supplier=supplier,
            reference_unit_cost=Decimal("1.75"),
            notes="Vendor June quote",
        )
        self.client.force_login(self.admin)

        list_response = self.client.get(reverse("supplier-product-cost-list"))
        form_response = self.client.get(reverse("supplier-product-cost-create"))

        self.assertEqual(list_response.status_code, 200)
        self.assertContains(list_response, "Product Default Cost")
        self.assertContains(list_response, "Supplier Reference Unit Cost")
        self.assertContains(list_response, "Vendor June quote")
        self.assertContains(list_response, "1.25")
        self.assertEqual(form_response.status_code, 200)
        self.assertContains(form_response, "Actual and landed costs are still recorded per received stock batch")
        self.assertContains(form_response, "Quote or expected vendor cost")

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
        cat = AnimalTypeOption.objects.get(code=Product.AnimalType.CAT)
        dog = AnimalTypeOption.objects.get(code=Product.AnimalType.DOG)
        tag = ProductTag.objects.create(name="Grain Free")
        product.life_stage = Product.LifeStage.ADULT
        product.save()
        product.animal_types.set([cat, dog])
        product.tags.add(tag)

        product.refresh_from_db()
        self.assertEqual(product.animal_type_labels, ["Cat", "Dog"])
        self.assertEqual(product.life_stage, "ADULT")
        self.assertEqual(list(product.tags.values_list("name", flat=True)), ["Grain Free"])

    def test_existing_product_without_classification_is_valid(self):
        product = Product.objects.create(product_code="P002", name="Plain Product")
        self.assertEqual(product.animal_type, "")
        self.assertEqual(product.life_stage, "")
        self.assertEqual(product.tags.count(), 0)

    def test_create_product_with_classification_and_tags_via_dashboard(self):
        cat = AnimalTypeOption.objects.get(code=Product.AnimalType.CAT)
        dog = AnimalTypeOption.objects.get(code=Product.AnimalType.DOG)
        tag1 = ProductTag.objects.create(name="Grain Free")
        tag2 = ProductTag.objects.create(name="Indoor")
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("product-create"),
            self._base_payload(animal_types=[cat.id, dog.id], life_stage="KITTEN", tags=[tag1.id, tag2.id]),
        )

        self.assertRedirects(response, reverse("product-list"))
        product = Product.objects.get(product_code="P010")
        self.assertEqual(product.animal_type, "CAT")
        self.assertEqual(set(product.animal_types.values_list("code", flat=True)), {"CAT", "DOG"})
        self.assertEqual(product.life_stage, "KITTEN")
        self.assertEqual(set(product.tags.values_list("name", flat=True)), {"Grain Free", "Indoor"})
        audit = AuditLog.objects.filter(action=AuditLog.Action.CREATE, module="catalog").latest("created_at")
        self.assertEqual(audit.new_value.get("animal_types"), ["Cat", "Dog"])
        self.assertEqual(audit.new_value.get("tags"), ["Grain Free", "Indoor"])

    def test_product_image_upload_persists_after_refresh(self):
        self.client.force_login(self.admin)
        image = tiny_image_upload()

        with TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            response = self.client.post(reverse("product-create"), self._base_payload(image=image))

            if response.status_code != 302:
                self.fail(response.context["form"].errors.as_text())
            self.assertRedirects(response, reverse("product-list"))
            product = Product.objects.get(product_code="P010")
            self.assertTrue(product.image.name.startswith("products/"))

            refresh = self.client.get(reverse("product-edit", kwargs={"product_id": product.pk}))
            self.assertContains(refresh, "Current image")
            self.assertContains(refresh, escape(product.image.url))
            self.assertTrue(product.image.name.endswith(".webp"))
            self.assertTrue(bool(product.image_thumb))

    def test_product_list_filters_by_animal_type_and_tag(self):
        dental = ProductTag.objects.create(name="Dental Care")
        cat = AnimalTypeOption.objects.get(code=Product.AnimalType.CAT)
        dog = AnimalTypeOption.objects.get(code=Product.AnimalType.DOG)
        reptile = AnimalTypeOption.objects.create(name="Reptile", code="REPTILE")
        cat_food = Product.objects.create(
            product_code="C1", name="Cat Food", animal_type=Product.AnimalType.CAT
        )
        cat_food.animal_types.add(cat)
        cat_food.tags.add(dental)
        dog_food = Product.objects.create(product_code="D1", name="Dog Food", animal_type=Product.AnimalType.DOG)
        dog_food.animal_types.add(dog)
        lizard_food = Product.objects.create(product_code="R1", name="Lizard Food", animal_type="REPTILE")
        lizard_food.animal_types.add(reptile)
        self.client.force_login(self.admin)

        by_animal = self.client.get(reverse("product-list"), {"animal_type": "CAT"})
        self.assertContains(by_animal, "Cat Food")
        self.assertNotContains(by_animal, "Dog Food")
        self.assertNotContains(by_animal, "Lizard Food")

        by_custom_animal = self.client.get(reverse("product-list"), {"animal_type": "REPTILE"})
        self.assertContains(by_custom_animal, "Reptile")
        self.assertContains(by_custom_animal, "Lizard Food")
        self.assertNotContains(by_custom_animal, "Cat Food")

        by_tag = self.client.get(reverse("product-list"), {"tag": dental.id})
        self.assertContains(by_tag, "Cat Food")
        self.assertNotContains(by_tag, "Dog Food")

    def test_product_form_renders_classification_fields(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse("product-create"))

        self.assertContains(response, 'name="animal_types"')
        self.assertContains(response, 'name="life_stage"')
        self.assertContains(response, 'name="tags"')


class ProductColumnFilterTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_superuser("pcf-admin", "a@x.com", "Admin123")
        self.cat = AnimalTypeOption.objects.get(code=Product.AnimalType.CAT)
        self.dog = AnimalTypeOption.objects.get(code=Product.AnimalType.DOG)
        self.cat_food = Product.objects.create(
            product_code="C1", name="Cat Food", animal_type=Product.AnimalType.CAT
        )
        self.cat_food.animal_types.add(self.cat)
        self.dog_food = Product.objects.create(
            product_code="D1", name="Dog Food", animal_type=Product.AnimalType.DOG
        )
        self.dog_food.animal_types.add(self.dog)
        self.bird_food = Product.objects.create(product_code="B1", name="Bird Seed")
        self.client.force_login(self.admin)

    def test_multi_select_status_or_within_column(self):
        # active OR inactive selected = show all (no narrowing)
        self.dog_food.is_active = False
        self.dog_food.save()
        response = self.client.get(reverse("product-list"), {"status": ["active", "inactive"]})
        self.assertContains(response, "Cat Food")
        self.assertContains(response, "Dog Food")

    def test_multi_select_animal_or_within_column(self):
        response = self.client.get(reverse("product-list"), {"animal_type": ["CAT", "DOG"]})
        self.assertContains(response, "Cat Food")
        self.assertContains(response, "Dog Food")
        self.assertNotContains(response, "Bird Seed")

    def test_filters_combine_as_and_across_columns(self):
        response = self.client.get(
            reverse("product-list"), {"animal_type": ["CAT", "DOG"], "q": "Cat"}
        )
        self.assertContains(response, "Cat Food")
        self.assertNotContains(response, "Dog Food")

    def test_active_filter_bar_renders_chip_with_remove_link(self):
        response = self.client.get(reverse("product-list"), {"animal_type": ["CAT"]})
        self.assertContains(response, "filter-bar")
        self.assertContains(response, "Animal")
        chips = response.context["active_filters"]
        self.assertEqual(len(chips), 1)
        self.assertNotIn("animal_type", chips[0]["remove_url"])

    def test_no_filter_bar_when_nothing_selected(self):
        response = self.client.get(reverse("product-list"))
        self.assertEqual(response.context["active_filters"], [])


class ProductImageWidgetTests(TestCase):
    """The media panel must stay a real, submitting file input.

    The whole design is progressive enhancement: media.js adds preview and
    drag-and-drop on top of a working <input type="file">. If the widget ever
    stops rendering that input — or stops honouring Django's clear-checkbox
    contract — uploads break silently for anyone whose JS did not load.
    """

    def setUp(self):
        self.user = get_user_model().objects.create_superuser(
            "imgowner", "imgowner@example.com", "Pw12345678"
        )
        self.client.force_login(self.user)

    def test_create_form_renders_a_real_file_input(self):
        html = self.client.get(reverse("product-create")).content.decode()
        self.assertIn('type="file"', html)
        self.assertIn('name="image"', html)
        self.assertIn("data-media-field", html)
        # Phones should open the camera rather than a file browser.
        self.assertIn('capture="environment"', html)
        self.assertIn('accept="image/*"', html)

    def test_widget_survives_storage_being_unreachable(self):
        """A dead media backend must not 500 the edit page.

        Asking a FieldFile for .url can raise when storage is misconfigured;
        the widget swallows that and renders without a preview instead of
        taking the whole form down.
        """
        from catalog.forms import ProductImageWidget

        class Boom:
            def __bool__(self):
                return True

            @property
            def url(self):
                raise OSError("storage down")

        ctx = ProductImageWidget().get_context("image", Boom(), {"id": "id_image"})
        self.assertEqual(ctx["current_url"], "")


class ProductViewToggleTests(TestCase):
    """Cards and table must be the SAME data, differently presented.

    The value of the toggle is that there is no second code path: one
    queryset, one paginator, one set of filters. If the grid ever starts
    rendering from something else, filters and pagination silently disagree
    between views — which is worse than not having the grid.
    """

    def setUp(self):
        self.user = get_user_model().objects.create_superuser(
            "gridowner", "gridowner@example.com", "Pw12345678"
        )
        self.client.force_login(self.user)
        category = Category.objects.create(name="Dog food")
        for i in range(3):
            Product.objects.create(
                product_code=f"GRID-{i}",
                name=f"Grid product {i}",
                category=category,
                unit="bag",
                default_selling_price=Decimal("9.50"),
            )

    def test_both_views_render_from_the_same_page(self):
        html = self.client.get(reverse("product-list")).content.decode()
        self.assertIn('data-view-panel="grid"', html)
        self.assertIn('data-view-panel="table"', html)
        # Every product appears in both panels of the one response.
        for i in range(3):
            self.assertEqual(html.count(f"GRID-{i}"), 2, f"GRID-{i} should appear in both views")

    def test_filters_apply_to_the_grid_too(self):
        html = self.client.get(reverse("product-list"), {"q": "Grid product 1"}).content.decode()
        self.assertEqual(html.count("GRID-1"), 2)
        self.assertNotIn("GRID-0", html)

    def test_table_is_the_default_view(self):
        """Bulk work is faster in a table; browsing is opt-in."""
        html = self.client.get(reverse("product-list")).content.decode()
        self.assertIn('data-view="table" aria-pressed="true"', html)
        self.assertIn('data-view="grid" aria-pressed="false"', html)
