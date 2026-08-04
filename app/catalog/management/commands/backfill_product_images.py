"""Backfill Product.image derivatives (capped WebP original + thumbnail).

IRREVERSIBLE: replaces stored Product.image bytes. Never touches barcode, QR,
KHQR, or logo images.

Default mode is dry-run. Writing requires ``--apply --confirm``.
"""

from django.core.management.base import BaseCommand, CommandError

from catalog.models import Product
from catalog.services import (
    ProductImageError,
    field_file_size,
    process_and_save_product_image,
    product_image_needs_processing,
)


class Command(BaseCommand):
    help = (
        "Downscale Product.image originals and generate image_thumb derivatives. "
        "Default is dry-run. Pass --apply --confirm to write (irreversible)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Write changes. Without this flag the command only reports (dry-run).",
        )
        parser.add_argument(
            "--confirm",
            action="store_true",
            help="Acknowledge that replacing stored originals is irreversible. Required with --apply.",
        )

    def handle(self, *args, **options):
        apply = options["apply"]
        confirm = options["confirm"]

        self.stdout.write(
            self.style.WARNING(
                "WARNING: This command replaces stored Product.image originals with "
                "downscaled WebP files. That rewrite is irreversible. "
                "Barcode, QR, KHQR, and logo images are never touched."
            )
        )

        products = (
            Product.objects.exclude(image="")
            .exclude(image__isnull=True)
            .order_by("pk")
        )
        candidates = [p for p in products if product_image_needs_processing(p)]
        skipped = products.count() - len(candidates)

        bytes_before = 0
        for product in candidates:
            bytes_before += field_file_size(product.image)
            bytes_before += field_file_size(product.image_thumb)

        self.stdout.write(f"Products with images: {products.count()}")
        self.stdout.write(f"Already processed (skip): {skipped}")
        self.stdout.write(f"Candidates to process: {len(candidates)}")
        self.stdout.write(f"Candidate bytes before: {bytes_before}")

        if not apply:
            self.stdout.write(
                self.style.WARNING(
                    "DRY RUN — nothing was written. Re-run with --apply --confirm to execute."
                )
            )
            return

        if not confirm:
            raise CommandError(
                "Refusing to write without --confirm. "
                "Replacing originals is irreversible. Pass --apply --confirm together."
            )

        processed = 0
        errors = 0
        bytes_after = 0
        for product in candidates:
            try:
                process_and_save_product_image(product)
                product.refresh_from_db()
                bytes_after += field_file_size(product.image)
                bytes_after += field_file_size(product.image_thumb)
                processed += 1
                self.stdout.write(f"  processed product pk={product.pk} ({product.product_code})")
            except ProductImageError as exc:
                errors += 1
                self.stderr.write(f"  FAILED product pk={product.pk}: {exc}")

        self.stdout.write(f"Processed: {processed}")
        self.stdout.write(f"Errors: {errors}")
        self.stdout.write(f"Bytes before: {bytes_before}")
        self.stdout.write(f"Bytes after: {bytes_after}")
        if bytes_before:
            saved = bytes_before - bytes_after
            pct = (saved / bytes_before) * 100
            self.stdout.write(f"Bytes saved: {saved} ({pct:.1f}%)")

        if errors:
            # Do not report success when images failed. An operator running this
            # over a whole catalogue must not see green text while photos were
            # skipped, because the run is irreversible for everything that did
            # succeed and the failures need attention before a re-run.
            raise CommandError(
                f"Backfill finished with {errors} failed image(s) out of "
                f"{len(candidates)} candidate(s). Review the FAILED lines above. "
                f"Successfully processed images have already been replaced."
            )
        self.stdout.write(self.style.SUCCESS("Backfill complete."))
