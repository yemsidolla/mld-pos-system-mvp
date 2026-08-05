"""Tests for Product.image derivatives — scope is Product photos only."""

from __future__ import annotations

import hashlib
from datetime import date, timedelta
from decimal import Decimal
from io import BytesIO
from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connection
from django.test import TestCase, TransactionTestCase, override_settings
from django.urls import reverse
from PIL import Image, ImageDraw

from catalog.models import Product, Supplier
from catalog.services import (
    ORIGINAL_MAX_EDGE,
    THUMB_MAX_EDGE,
    ProductImageError,
    process_and_save_product_image,
    process_product_image,
    product_image_needs_processing,
)
from core.models import StoreSetting
from core.permissions import ADMIN_GROUP
from inventory.models import StockBatch
from inventory.services import receive_stock


def _image_upload(size, *, mode="RGB", color="red", name="photo.png", fmt="PNG", exif=None):
    image = Image.new(mode, size, color=color)
    if mode == "P":
        image = Image.new("RGB", size, color=color).convert("P")
    buffer = BytesIO()
    save_kwargs = {"format": fmt}
    if exif is not None:
        save_kwargs["exif"] = exif
    if fmt.upper() == "JPEG" and mode == "RGBA":
        image = image.convert("RGB")
    image.save(buffer, **save_kwargs)
    content_type = {
        "PNG": "image/png",
        "JPEG": "image/jpeg",
        "WEBP": "image/webp",
    }.get(fmt.upper(), "application/octet-stream")
    return SimpleUploadedFile(name, buffer.getvalue(), content_type=content_type)


def _oriented_upload():
    """Wide red|blue strip tagged Orientation=6 (rotate 90 CW for display)."""
    image = Image.new("RGB", (200, 100), color="red")
    draw = ImageDraw.Draw(image)
    draw.rectangle([100, 0, 200, 100], fill="blue")
    exif = image.getexif()
    exif[274] = 6  # Orientation
    buffer = BytesIO()
    image.save(buffer, format="JPEG", exif=exif)
    return SimpleUploadedFile("rotated.jpg", buffer.getvalue(), content_type="image/jpeg")


def _file_md5(field_file) -> str:
    field_file.open("rb")
    try:
        digest = hashlib.md5(field_file.read()).hexdigest()
    finally:
        field_file.close()
    return digest


MEDIA_SETTINGS = {
    "USE_S3_MEDIA": False,
    "STORAGES": {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    },
}


@override_settings(**MEDIA_SETTINGS)
class ProductImageServiceTests(TestCase):
    def test_oversized_image_is_capped_and_thumb_created(self):
        upload = _image_upload((4000, 3000), name="huge.png")
        processed = process_product_image(upload)
        original = Image.open(processed.original)
        thumb = Image.open(processed.thumb)
        self.assertEqual(original.format, "WEBP")
        self.assertEqual(thumb.format, "WEBP")
        self.assertLessEqual(max(original.size), ORIGINAL_MAX_EDGE)
        self.assertLessEqual(max(thumb.size), THUMB_MAX_EDGE)
        self.assertEqual(original.size[0] / original.size[1], 4000 / 3000)

    def test_already_small_image_is_not_upscaled(self):
        upload = _image_upload((40, 30), name="tiny.png")
        processed = process_product_image(upload)
        original = Image.open(processed.original)
        thumb = Image.open(processed.thumb)
        self.assertEqual(original.size, (40, 30))
        self.assertEqual(thumb.size, (40, 30))

    def test_non_square_aspect_preserved(self):
        upload = _image_upload((1600, 400), name="wide.png")
        processed = process_product_image(upload)
        original = Image.open(processed.original)
        self.assertEqual(original.size, (1600, 400))
        thumb = Image.open(processed.thumb)
        self.assertEqual(max(thumb.size), THUMB_MAX_EDGE)
        self.assertAlmostEqual(thumb.size[0] / thumb.size[1], 4.0, places=1)

    def test_rgba_palette_cmyk_greyscale_encode(self):
        cases = [
            _image_upload((120, 80), mode="RGBA", color=(255, 0, 0, 128), name="a.png"),
            _image_upload((120, 80), mode="P", color="green", name="p.png"),
            _image_upload((120, 80), mode="CMYK", color=(0, 50, 50, 0), name="c.jpg", fmt="JPEG"),
            _image_upload((120, 80), mode="L", color=128, name="g.png"),
        ]
        for upload in cases:
            with self.subTest(name=upload.name):
                processed = process_product_image(upload)
                image = Image.open(processed.original)
                self.assertEqual(image.format, "WEBP")
                self.assertIn(image.mode, ("RGB", "RGBA"))
                # Not a solid black failure mode
                extrema = image.convert("RGB").getextrema()
                self.assertTrue(any(channel[1] > 0 for channel in extrema))

    def test_corrupt_upload_raises_clean_error(self):
        upload = SimpleUploadedFile("bad.png", b"not-an-image", content_type="image/png")
        with self.assertRaises(ProductImageError):
            process_product_image(upload)

    def test_exif_orientation_is_applied(self):
        upload = _oriented_upload()
        processed = process_product_image(upload)
        original = Image.open(processed.original)
        # Orientation 6 rotates 90 CW: stored 200x100 becomes displayed 100x200.
        self.assertEqual(original.size, (100, 200))
        # After transpose, left column should be red (was top of stored? Orientation 6:
        # row 0 of stored becomes right column after CW rotate... verify not sideways 200x100.
        self.assertLess(original.size[0], original.size[1])
        self.assertFalse(original.getexif().get(274))

    def test_filenames_with_spaces_and_unicode(self):
        upload = _image_upload((80, 80), name="my photo 猫.png")
        processed = process_product_image(upload)
        self.assertEqual(processed.original_name, "my photo 猫.webp")
        self.assertEqual(processed.thumb_name, "my photo 猫.webp")

    def test_exif_gps_stripped_from_output(self):
        image = Image.new("RGB", (64, 64), color="orange")
        exif = image.getexif()
        exif[274] = 1
        # GPS IFD tag 34853 — presence in source; output must not carry EXIF blob.
        buffer = BytesIO()
        image.save(buffer, format="JPEG", exif=exif)
        upload = SimpleUploadedFile("gps.jpg", buffer.getvalue(), content_type="image/jpeg")
        processed = process_product_image(upload)
        out = Image.open(processed.original)
        self.assertEqual(dict(out.getexif()), {})


@override_settings(**MEDIA_SETTINGS)
class ProductImageRegressionGuardTests(TestCase):
    """Barcode / QR / KHQR / logo must remain byte-identical."""

    def setUp(self):
        self.media = TemporaryDirectory()
        self.addCleanup(self.media.cleanup)
        self.override = override_settings(MEDIA_ROOT=self.media.name, **MEDIA_SETTINGS)
        self.override.enable()
        self.addCleanup(self.override.disable)

        self.user = get_user_model().objects.create_user(username="img-admin", password="x")
        self.product = Product.objects.create(
            product_code="IMG1",
            name="Image Product",
            original_barcode="8859999000001",
        )
        self.supplier = Supplier.objects.create(name="Image Supplier")

        setting = StoreSetting.load()
        setting.logo.save("logo.png", _image_upload((200, 80), name="logo.png"), save=False)
        setting.khqr_image.save("khqr.png", _image_upload((180, 180), name="khqr.png"), save=False)
        setting.save()
        self.setting = setting

        batch, _movement = receive_stock(
            product=self.product,
            supplier=self.supplier,
            quantity=5,
            expiry_date=date.today() + timedelta(days=30),
            actual_unit_cost=Decimal("1.00"),
            selling_price=Decimal("2.00"),
            received_by=self.user,
        )
        self.batch = StockBatch.objects.get(pk=batch.pk)

        self.checksums = {
            "barcode": _file_md5(self.batch.barcode_image),
            "qr": _file_md5(self.batch.qr_image),
            "khqr": _file_md5(self.setting.khqr_image),
            "logo": _file_md5(self.setting.logo),
        }

    def _assert_protected_unchanged(self):
        self.batch.refresh_from_db()
        self.setting.refresh_from_db()
        self.assertEqual(_file_md5(self.batch.barcode_image), self.checksums["barcode"])
        self.assertEqual(_file_md5(self.batch.qr_image), self.checksums["qr"])
        self.assertEqual(_file_md5(self.setting.khqr_image), self.checksums["khqr"])
        self.assertEqual(_file_md5(self.setting.logo), self.checksums["logo"])

    def test_processing_product_image_leaves_protected_files_byte_identical(self):
        self.product.image = _image_upload((800, 600), name="product.png")
        self.product.save()
        process_and_save_product_image(self.product)
        self._assert_protected_unchanged()

    def test_backfill_leaves_protected_files_byte_identical(self):
        self.product.image = _image_upload((1200, 900), name="product.png")
        self.product.save()
        call_command("backfill_product_images", apply=True, confirm=True)
        self._assert_protected_unchanged()


@override_settings(**MEDIA_SETTINGS)
class ProductImageTemplateTests(TestCase):
    def setUp(self):
        self.media = TemporaryDirectory()
        self.addCleanup(self.media.cleanup)
        self.override = override_settings(MEDIA_ROOT=self.media.name, **MEDIA_SETTINGS)
        self.override.enable()
        self.addCleanup(self.override.disable)

        self.admin = get_user_model().objects.create_user(username="thumb-admin", password="x")
        group, _ = Group.objects.get_or_create(name=ADMIN_GROUP)
        self.admin.groups.add(group)
        self.product = Product.objects.create(product_code="T1", name="Thumb Product")

    def test_list_uses_thumb_when_present(self):
        self.product.image = _image_upload((200, 200), name="full.png")
        self.product.save()
        process_and_save_product_image(self.product)
        self.client.force_login(self.admin)
        response = self.client.get(reverse("product-list"))
        self.assertContains(response, self.product.image_thumb.url)
        self.assertNotContains(response, "product-thumb-empty")

    def test_list_falls_back_to_image_when_thumb_missing(self):
        self.product.image = _image_upload((50, 50), name="only.png")
        self.product.save()
        self.assertFalse(bool(self.product.image_thumb))
        self.client.force_login(self.admin)
        response = self.client.get(reverse("product-list"))
        self.assertContains(response, self.product.image.name)
        self.assertNotContains(response, "product-thumb-empty")


@override_settings(**MEDIA_SETTINGS)
class ProductImageUploadFormTests(TestCase):
    def setUp(self):
        self.media = TemporaryDirectory()
        self.addCleanup(self.media.cleanup)
        self.override = override_settings(MEDIA_ROOT=self.media.name, **MEDIA_SETTINGS)
        self.override.enable()
        self.addCleanup(self.override.disable)

        self.admin = get_user_model().objects.create_user(username="form-admin", password="x")
        group, _ = Group.objects.get_or_create(name=ADMIN_GROUP)
        self.admin.groups.add(group)

    def test_new_upload_creates_webp_original_and_thumb(self):
        self.client.force_login(self.admin)
        upload = _image_upload((2000, 1500), name="camera.png")
        response = self.client.post(
            reverse("product-create"),
            {
                "product_code": "UP1",
                "name": "Upload Product",
                "unit": "Unit",
                "default_cost_price": "1.00",
                "default_selling_price": "2.00",
                "min_stock": "0",
                "is_active": "on",
                "image": upload,
            },
        )
        self.assertEqual(response.status_code, 302, getattr(response, "context", None))
        product = Product.objects.get(product_code="UP1")
        self.assertTrue(product.image.name.endswith(".webp"))
        self.assertTrue(product.image_thumb.name.startswith("products/thumbs/"))
        with product.image.open("rb") as handle:
            original = Image.open(handle)
            original.load()
            self.assertLessEqual(max(original.size), ORIGINAL_MAX_EDGE)
        with product.image_thumb.open("rb") as handle:
            thumb = Image.open(handle)
            thumb.load()
            self.assertLessEqual(max(thumb.size), THUMB_MAX_EDGE)

    def test_corrupt_upload_returns_validation_error_not_500(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("product-create"),
            {
                "product_code": "UP2",
                "name": "Bad Upload",
                "unit": "Unit",
                "default_cost_price": "1.00",
                "default_selling_price": "2.00",
                "min_stock": "0",
                "is_active": "on",
                "image": SimpleUploadedFile("bad.png", b"nope", content_type="image/png"),
            },
        )
        self.assertEqual(response.status_code, 200)
        form = response.context["form"]
        self.assertTrue(form.errors.get("image"))
        self.assertFalse(Product.objects.filter(product_code="UP2").exists())


@override_settings(**MEDIA_SETTINGS)
class ProductImageBackfillTests(TestCase):
    def setUp(self):
        self.media = TemporaryDirectory()
        self.addCleanup(self.media.cleanup)
        self.override = override_settings(MEDIA_ROOT=self.media.name, **MEDIA_SETTINGS)
        self.override.enable()
        self.addCleanup(self.override.disable)

        self.product = Product.objects.create(product_code="BF1", name="Backfill Product")
        self.product.image = _image_upload((1800, 1200), name="raw.png")
        self.product.save()
        self.original_name = self.product.image.name
        self.original_bytes = self.product.image.size

    def test_dry_run_writes_nothing(self):
        call_command("backfill_product_images")
        self.product.refresh_from_db()
        self.assertEqual(self.product.image.name, self.original_name)
        self.assertFalse(bool(self.product.image_thumb))
        self.assertEqual(self.product.image.size, self.original_bytes)

    def test_apply_is_idempotent(self):
        call_command("backfill_product_images", apply=True, confirm=True)
        self.product.refresh_from_db()
        self.assertTrue(product_image_needs_processing(self.product) is False)
        thumb_name = self.product.image_thumb.name
        image_name = self.product.image.name
        image_size = self.product.image.size
        thumb_size = self.product.image_thumb.size

        call_command("backfill_product_images", apply=True, confirm=True)
        self.product.refresh_from_db()
        self.assertEqual(self.product.image.name, image_name)
        self.assertEqual(self.product.image_thumb.name, thumb_name)
        self.assertEqual(self.product.image.size, image_size)
        self.assertEqual(self.product.image_thumb.size, thumb_size)

    def test_apply_raises_when_an_image_cannot_be_processed(self):
        """A failed image must not be reported as a successful backfill.

        The rewrite is irreversible for everything that did succeed, so an
        operator running this across the catalogue has to be told that some
        photos were skipped rather than seeing a success message.
        """
        broken = Product.objects.create(product_code="BF2", name="Broken Image")
        broken.image.save(
            "broken.png",
            SimpleUploadedFile("broken.png", b"not-an-image", content_type="image/png"),
            save=True,
        )
        broken_name = broken.image.name

        with self.assertRaises(CommandError) as ctx:
            call_command("backfill_product_images", apply=True, confirm=True)

        self.assertIn("failed image", str(ctx.exception))

        # The healthy product was still processed — failures are isolated, and
        # the successful rewrites are what the error message warns about.
        self.product.refresh_from_db()
        self.assertFalse(product_image_needs_processing(self.product))

        # The broken source is left untouched rather than half-written.
        broken.refresh_from_db()
        self.assertEqual(broken.image.name, broken_name)
        self.assertFalse(bool(broken.image_thumb))


class ProductImageThumbMigrationTests(TransactionTestCase):
    def _has_image_thumb_column(self):
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT 1
                FROM information_schema.columns
                WHERE table_name = 'catalog_product'
                  AND column_name = 'image_thumb'
                """
            )
            return cursor.fetchone() is not None

    def test_migration_forward_and_backward(self):
        call_command("migrate", "catalog", "0004_animaltypeoption_product_animal_types", verbosity=0)
        self.assertFalse(self._has_image_thumb_column())

        call_command("migrate", "catalog", "0005_product_image_thumb", verbosity=0)
        self.assertTrue(self._has_image_thumb_column())

        call_command("migrate", "catalog", "0004_animaltypeoption_product_animal_types", verbosity=0)
        self.assertFalse(self._has_image_thumb_column())

        call_command("migrate", "catalog", "0005_product_image_thumb", verbosity=0)
        self.assertTrue(self._has_image_thumb_column())
