from decimal import Decimal
from io import BytesIO
from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from openpyxl import Workbook

from audit.models import AuditLog
from catalog.models import AnimalTypeOption, Brand, Category, Product, ProductTag, Supplier
from core.permissions import CASHIER_GROUP
from inventory.models import InventoryMovement, StockBatch

from .models import BatchUploadJob
from .services import (
    commit_upload_job,
    create_upload_job,
    delete_upload_row,
    get_template_csv,
    parse_upload_file,
    update_upload_row,
)


def csv_upload(name, content):
    return SimpleUploadedFile(name, content.encode("utf-8"), content_type="text/csv")


def xlsx_upload(name, headers, rows):
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.append(headers)
    for row in rows:
        worksheet.append(row)
    buffer = BytesIO()
    workbook.save(buffer)
    return SimpleUploadedFile(
        name,
        buffer.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


class BatchUploadParsingTests(TestCase):
    def test_csv_parsing_reads_headers_rows_and_row_numbers(self):
        upload = csv_upload("categories.csv", "name,description,is_active\nFood,Pet food,TRUE\n")

        headers, rows = parse_upload_file(upload)

        self.assertEqual(headers, ["name", "description", "is_active"])
        self.assertEqual(rows[0][0], 2)
        self.assertEqual(rows[0][1]["name"], "Food")

    def test_xlsx_parsing_reads_headers_rows_and_dates(self):
        upload = xlsx_upload(
            "stock_in.xlsx",
            [
                "product_code",
                "supplier",
                "quantity",
                "expiry_date",
                "actual_unit_cost",
                "landed_unit_cost",
                "selling_price",
                "note",
            ],
            [["P001", "Pet Wholesale", 5, "2027-06-01", "1.50", "1.75", "2.50", "Initial stock"]],
        )

        headers, rows = parse_upload_file(upload)

        self.assertEqual(headers[0], "product_code")
        self.assertEqual(rows[0][0], 2)
        self.assertEqual(rows[0][1]["expiry_date"], "2027-06-01")

    def test_template_csv_contains_target_schema_and_sample_row(self):
        template_csv = get_template_csv(BatchUploadJob.Target.PRODUCTS)

        self.assertIn("product_code,original_barcode,name,category,brand", template_csv)
        self.assertIn("P001", template_csv)


class BatchUploadServiceTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_user(
            username="batch-admin",
            password="Admin123",
            is_staff=True,
            is_superuser=True,
        )
        self.cashier = get_user_model().objects.create_user(username="cashier", password="Admin123")
        cashier_group, _created = Group.objects.get_or_create(name=CASHIER_GROUP)
        self.cashier.groups.add(cashier_group)
        self.category = Category.objects.create(name="Food", description="Old food")
        self.brand = Brand.objects.create(name="Melodu", description="Old brand")
        self.supplier = Supplier.objects.create(name="Pet Wholesale", contact_person="Old contact")
        self.product = Product.objects.create(
            product_code="P001",
            original_barcode="8851234567890",
            name="Cat Food",
            category=self.category,
            brand=self.brand,
            default_cost_price=Decimal("1.50"),
            default_selling_price=Decimal("2.50"),
            min_stock=5,
        )

    def test_missing_schema_columns_are_rejected(self):
        upload = csv_upload("products.csv", "product_code,name\nP002,Dog Food\n")

        with self.assertRaisesMessage(ValidationError, "Missing columns"):
            create_upload_job(target=BatchUploadJob.Target.PRODUCTS, uploaded_file=upload, uploaded_by=self.admin)

    def test_preview_creates_upload_job_and_row_records(self):
        upload = csv_upload(
            "categories.csv",
            "name,description,is_active\nTreats,Pet treats,TRUE\nToys,Pet toys,FALSE\n",
        )

        job = create_upload_job(target=BatchUploadJob.Target.CATEGORIES, uploaded_file=upload, uploaded_by=self.admin)

        self.assertEqual(job.status, BatchUploadJob.Status.PREVIEW)
        self.assertEqual(job.rows.count(), 2)
        self.assertEqual(job.rows.first().normalized_data["is_active"], True)
        self.assertEqual(job.rows.last().normalized_data["is_active"], False)
        self.assertEqual(job.rows.first().validation_errors, [])

    def test_row_edit_updates_staged_normalized_data(self):
        upload = csv_upload("categories.csv", "name,description,is_active\n,Needs name,TRUE\n")
        job = create_upload_job(target=BatchUploadJob.Target.CATEGORIES, uploaded_file=upload, uploaded_by=self.admin)
        row = job.rows.get()
        self.assertIn("name: required", row.validation_errors)

        updated = update_upload_row(row, {"name": "Toys", "description": "Pet toys", "is_active": "FALSE"})

        self.assertEqual(updated.normalized_data["name"], "Toys")
        self.assertEqual(updated.normalized_data["is_active"], False)
        self.assertEqual(updated.validation_errors, [])

    def test_row_delete_excludes_row_from_commit(self):
        upload = csv_upload(
            "categories.csv",
            "name,description,is_active\nSkip Me,Should not commit,TRUE\nKeep Me,Should commit,TRUE\n",
        )
        job = create_upload_job(target=BatchUploadJob.Target.CATEGORIES, uploaded_file=upload, uploaded_by=self.admin)
        delete_upload_row(job.rows.get(row_number=2))

        committed = commit_upload_job(job=job, committed_by=self.admin)

        self.assertFalse(Category.objects.filter(name="Skip Me").exists())
        self.assertTrue(Category.objects.filter(name="Keep Me").exists())
        self.assertEqual(committed.summary["skipped"], 1)
        self.assertEqual(committed.summary["created"], 1)

    def test_category_brand_supplier_and_product_commits_update_existing_records(self):
        category_job = create_upload_job(
            target=BatchUploadJob.Target.CATEGORIES,
            uploaded_file=csv_upload("categories.csv", "name,description,is_active\nFood,Fresh food,FALSE\n"),
            uploaded_by=self.admin,
        )
        brand_job = create_upload_job(
            target=BatchUploadJob.Target.BRANDS,
            uploaded_file=csv_upload("brands.csv", "name,description,is_active\nMelodu,Updated brand,TRUE\n"),
            uploaded_by=self.admin,
        )
        supplier_job = create_upload_job(
            target=BatchUploadJob.Target.SUPPLIERS,
            uploaded_file=csv_upload(
                "suppliers.csv",
                "name,contact_person,phone,telegram,address,notes,is_active\n"
                "Pet Wholesale,Sophea,012345678,@supplier,Phnom Penh,Updated,TRUE\n",
            ),
            uploaded_by=self.admin,
        )
        product_job = create_upload_job(
            target=BatchUploadJob.Target.PRODUCTS,
            uploaded_file=csv_upload(
                "products.csv",
                "product_code,original_barcode,name,category,brand,unit,default_cost_price,"
                "default_selling_price,min_stock,description,is_active\n"
                "P001,8851234567890,Updated Cat Food,Food,Melodu,Bag,1.75,2.95,8,Updated,TRUE\n",
            ),
            uploaded_by=self.admin,
        )

        for job in [category_job, brand_job, supplier_job, product_job]:
            commit_upload_job(job=job, committed_by=self.admin)

        self.category.refresh_from_db()
        self.brand.refresh_from_db()
        self.supplier.refresh_from_db()
        self.product.refresh_from_db()

        self.assertEqual(Category.objects.filter(name="Food").count(), 1)
        self.assertEqual(self.category.description, "Fresh food")
        self.assertFalse(self.category.is_active)
        self.assertEqual(self.brand.description, "Updated brand")
        self.assertEqual(self.supplier.contact_person, "Sophea")
        self.assertEqual(Product.objects.filter(product_code="P001").count(), 1)
        self.assertEqual(self.product.name, "Updated Cat Food")
        self.assertEqual(self.product.default_selling_price, Decimal("2.95"))
        self.assertEqual(self.product.min_stock, 8)

    def test_product_original_barcode_uniqueness_failure_appears_in_preview(self):
        upload = csv_upload(
            "products.csv",
            "product_code,original_barcode,name,category,brand,unit,default_cost_price,"
            "default_selling_price,min_stock,description,is_active\n"
            "P002,8851234567890,Dog Food,Food,Melodu,Bag,1.00,2.00,3,,TRUE\n",
        )

        job = create_upload_job(target=BatchUploadJob.Target.PRODUCTS, uploaded_file=upload, uploaded_by=self.admin)

        self.assertIn("original_barcode: already used by another product", job.rows.get().validation_errors)

    def test_product_original_barcode_duplicate_inside_upload_is_invalid(self):
        upload = csv_upload(
            "products.csv",
            "product_code,original_barcode,name,category,brand,unit,default_cost_price,"
            "default_selling_price,min_stock,description,is_active\n"
            "P002,8850000000001,Dog Food,Food,Melodu,Bag,1.00,2.00,3,,TRUE\n"
            "P003,8850000000001,Cat Toy,Food,Melodu,Piece,0.50,1.50,2,,TRUE\n",
        )

        job = create_upload_job(target=BatchUploadJob.Target.PRODUCTS, uploaded_file=upload, uploaded_by=self.admin)

        for row in job.rows.all():
            self.assertIn("original_barcode: duplicate in upload file", row.validation_errors)

    def test_stock_in_upload_uses_receive_stock_outputs(self):
        upload = csv_upload(
            "stock_in.csv",
            "product_code,supplier,quantity,expiry_date,actual_unit_cost,landed_unit_cost,selling_price,note\n"
            "P001,Pet Wholesale,7,2027-06-01,1.60,1.85,2.70,Bulk stock\n",
        )
        job = create_upload_job(target=BatchUploadJob.Target.STOCK_IN, uploaded_file=upload, uploaded_by=self.admin)
        self.assertEqual(job.rows.get().validation_errors, [])

        with TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            commit_upload_job(job=job, committed_by=self.admin)

        stock_batch = StockBatch.objects.get(product=self.product)
        self.assertEqual(stock_batch.quantity_received, 7)
        self.assertEqual(stock_batch.quantity_available, 7)
        self.assertEqual(stock_batch.actual_unit_cost, Decimal("1.60"))
        self.assertEqual(stock_batch.landed_unit_cost, Decimal("1.85"))
        self.assertEqual(stock_batch.custom_code, f"8851234567890-M-270601-{stock_batch.batch_no}")
        self.assertTrue(stock_batch.barcode_image.name.endswith(".png"))
        self.assertTrue(stock_batch.qr_image.name.endswith(".png"))
        self.assertTrue(InventoryMovement.objects.filter(movement_type=InventoryMovement.MovementType.STOCK_IN).exists())
        self.assertTrue(AuditLog.objects.filter(action=AuditLog.Action.STOCK_IN).exists())
        self.assertTrue(AuditLog.objects.filter(module="batch_upload").exists())

    def test_stock_in_upload_accepts_missing_optional_landed_cost_column(self):
        upload = csv_upload(
            "stock_in.csv",
            "product_code,supplier,quantity,expiry_date,actual_unit_cost,selling_price,note\n"
            "P001,Pet Wholesale,7,2027-06-01,1.60,2.70,Bulk stock\n",
        )

        job = create_upload_job(target=BatchUploadJob.Target.STOCK_IN, uploaded_file=upload, uploaded_by=self.admin)

        self.assertEqual(job.rows.get().validation_errors, [])
        self.assertEqual(job.rows.get().normalized_data["landed_unit_cost"], "")

    def test_invalid_rows_cannot_be_committed(self):
        upload = csv_upload(
            "stock_in.csv",
            "product_code,supplier,quantity,expiry_date,actual_unit_cost,landed_unit_cost,selling_price,note\n"
            "MISSING,Pet Wholesale,7,2027-06-01,1.60,,2.70,Bulk stock\n",
        )
        job = create_upload_job(target=BatchUploadJob.Target.STOCK_IN, uploaded_file=upload, uploaded_by=self.admin)

        with self.assertRaisesMessage(ValidationError, "No valid selected rows"):
            commit_upload_job(job=job, committed_by=self.admin)

        self.assertEqual(StockBatch.objects.count(), 0)


class BatchUploadViewTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_user(
            username="view-admin",
            password="Admin123",
            is_staff=True,
            is_superuser=True,
        )
        self.cashier = get_user_model().objects.create_user(username="view-cashier", password="Admin123")
        cashier_group, _created = Group.objects.get_or_create(name=CASHIER_GROUP)
        self.cashier.groups.add(cashier_group)

    def test_batch_upload_pages_are_admin_only(self):
        self.client.force_login(self.cashier)
        cashier_response = self.client.get(reverse("batch-upload"))
        self.assertEqual(cashier_response.status_code, 403)
        self.assertContains(cashier_response, "Access denied", status_code=403)

        self.client.force_login(self.admin)
        admin_response = self.client.get(reverse("batch-upload"))
        self.assertEqual(admin_response.status_code, 200)
        self.assertContains(admin_response, "Batch Upload")

    @override_settings(DEBUG=False, ALLOWED_HOSTS=["testserver"])
    def test_invalid_template_target_renders_friendly_404(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse("batch-upload-template", kwargs={"target": "missing"}))

        self.assertEqual(response.status_code, 404)
        self.assertContains(response, "Page or item not found", status_code=404)

    def test_admin_can_upload_preview_edit_delete_and_commit(self):
        self.client.force_login(self.admin)
        upload = csv_upload(
            "categories.csv",
            "name,description,is_active\nView First,Before edit,TRUE\nView Second,Delete me,TRUE\n",
        )

        upload_response = self.client.post(
            reverse("batch-upload"),
            {"target": BatchUploadJob.Target.CATEGORIES, "file": upload},
        )
        self.assertEqual(upload_response.status_code, 302)
        job = BatchUploadJob.objects.get()
        rows = list(job.rows.order_by("row_number"))

        edit_response = self.client.post(
            reverse("batch-upload-row-update", kwargs={"job_id": job.id, "row_id": rows[0].id}),
            {"name": "View Edited", "description": "After edit", "is_active": "TRUE"},
        )
        delete_response = self.client.post(
            reverse("batch-upload-row-delete", kwargs={"job_id": job.id, "row_id": rows[1].id}),
        )
        commit_response = self.client.post(reverse("batch-upload-commit", kwargs={"job_id": job.id}))

        self.assertEqual(edit_response.status_code, 302)
        self.assertEqual(delete_response.status_code, 302)
        self.assertEqual(commit_response.status_code, 302)
        self.assertTrue(Category.objects.filter(name="View Edited", description="After edit").exists())
        self.assertFalse(Category.objects.filter(name="View Second").exists())

    def test_django_admin_home_links_to_batch_upload_workflow(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse("admin:index"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Melodu Workflows")
        self.assertContains(response, reverse("batch-upload"))


class ProductClassificationUploadTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_user(
            username="class-upload-admin", password="Admin123", is_staff=True, is_superuser=True
        )
        Category.objects.create(name="Food")
        Brand.objects.create(name="Melodu")

    def test_upload_with_classification_columns_commits_tags(self):
        content = (
            "product_code,original_barcode,name,category,brand,unit,default_cost_price,"
            "default_selling_price,min_stock,description,animal_type,life_stage,tags,is_active\n"
            "P100,8850000001000,Kitten Food,Food,Melodu,Bag,1.50,2.50,3,,cat; dog,kitten,Grain Free; Indoor,TRUE\n"
        )
        job = create_upload_job(
            target=BatchUploadJob.Target.PRODUCTS,
            uploaded_file=csv_upload("products.csv", content),
            uploaded_by=self.admin,
        )
        self.assertEqual(job.rows.get().validation_errors, [])

        commit_upload_job(job=job, committed_by=self.admin)

        product = Product.objects.get(product_code="P100")
        self.assertEqual(product.animal_type, "CAT")
        self.assertEqual(set(product.animal_types.values_list("code", flat=True)), {"CAT", "DOG"})
        self.assertEqual(product.life_stage, "KITTEN")
        self.assertEqual(set(product.tags.values_list("name", flat=True)), {"Grain Free", "Indoor"})
        self.assertEqual(ProductTag.objects.filter(name__in=["Grain Free", "Indoor"]).count(), 2)
        self.assertEqual(AnimalTypeOption.objects.filter(code__in=["CAT", "DOG"]).count(), 2)

    def test_upload_without_optional_columns_still_works(self):
        content = (
            "product_code,original_barcode,name,category,brand,unit,default_cost_price,"
            "default_selling_price,min_stock,description,is_active\n"
            "P101,8850000001001,Dog Food,Food,Melodu,Bag,1.50,2.50,3,,TRUE\n"
        )
        job = create_upload_job(
            target=BatchUploadJob.Target.PRODUCTS,
            uploaded_file=csv_upload("products.csv", content),
            uploaded_by=self.admin,
        )
        self.assertEqual(job.rows.get().validation_errors, [])

        commit_upload_job(job=job, committed_by=self.admin)

        product = Product.objects.get(product_code="P101")
        self.assertEqual(product.animal_type, "")
        self.assertEqual(product.tags.count(), 0)

    def test_invalid_animal_type_is_flagged(self):
        content = (
            "product_code,original_barcode,name,category,brand,unit,default_cost_price,"
            "default_selling_price,min_stock,description,animal_type,life_stage,tags,is_active\n"
            "P102,8850000001002,Mystery,Food,Melodu,Bag,1.50,2.50,3,,DINOSAUR,,,TRUE\n"
        )
        job = create_upload_job(
            target=BatchUploadJob.Target.PRODUCTS,
            uploaded_file=csv_upload("products.csv", content),
            uploaded_by=self.admin,
        )
        self.assertIn("animal_type: invalid value", job.rows.get().validation_errors)
