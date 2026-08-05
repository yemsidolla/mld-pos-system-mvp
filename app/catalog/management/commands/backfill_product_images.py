"""Backfill Product.image derivatives (capped WebP original + thumbnail).

IRREVERSIBLE: replaces stored Product.image bytes. Never touches barcode, QR,
KHQR, or logo images.

Default mode is dry-run. Writing requires ``--apply --confirm``.

Concurrency caveat (documented, not fixed): a concurrent non-image product
edit can still write back a stale image name. The form reads image A, blocks
on the backfill row lock, then saves all fields including stale A after
backfill committed B and deleted A. Quiesce product create/edit while this
command runs.
"""

from django.core.management.base import BaseCommand, CommandError

from catalog.models import Product
from catalog.services import (
    ProductImageError,
    field_file_size,
    process_and_save_product_image,
    process_product_image,
    product_image_needs_processing,
)


class Command(BaseCommand):
    help = (
        "Downscale Product.image originals and generate image_thumb derivatives. "
        "Default is dry-run. Pass --apply --confirm to write (irreversible). "
        "Quiesce product create/edit while this runs: a concurrent non-image "
        "edit can still overwrite a backfilled image name with a stale value."
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
                "Barcode, QR, KHQR, and logo images are never touched. "
                "Quiesce product create/edit for the duration of this run — a concurrent "
                "non-image product edit can still write back a stale image filename "
                "after backfill replaced and deleted the previous file."
            )
        )

        products = (
            Product.objects.exclude(image="")
            .exclude(image__isnull=True)
            .order_by("pk")
        )
        # Count without retaining FieldFile handles for every row.
        total_with_images = products.count()
        candidate_count = 0
        skipped = 0

        if not apply:
            # Preflight: decode each candidate lazily so operators learn which
            # images would fail before any irreversible rewrite (F9). Close each
            # file after decoding so a large catalogue cannot exhaust FDs (R6).
            would_fail = 0
            for product in products.iterator(chunk_size=50):
                if not product_image_needs_processing(product):
                    skipped += 1
                    continue
                candidate_count += 1
                try:
                    process_product_image(product.image, source_name=product.image.name)
                except ProductImageError as exc:
                    would_fail += 1
                    self.stderr.write(f"  WOULD FAIL product pk={product.pk}: {exc}")
                finally:
                    image_field = getattr(product, "image", None)
                    if image_field is not None and hasattr(image_field, "close"):
                        try:
                            image_field.close()
                        except Exception:
                            pass

            self.stdout.write(f"Products with images: {total_with_images}")
            self.stdout.write(f"Already processed (skip): {skipped}")
            self.stdout.write(f"Candidates to process: {candidate_count}")
            self.stdout.write(f"Dry-run decode failures: {would_fail}")
            self.stdout.write(
                self.style.WARNING(
                    "DRY RUN — nothing was written. Re-run with --apply --confirm to execute."
                )
            )
            if would_fail:
                raise CommandError(
                    f"Dry-run found {would_fail} image(s) that would fail processing. "
                    "Fix or remove them before running --apply --confirm."
                )
            return

        if not confirm:
            raise CommandError(
                "Refusing to write without --confirm. "
                "Replacing originals is irreversible. Pass --apply --confirm together."
            )

        # Apply path: materialise candidate pks first (names only), then process
        # one row at a time so we do not hold every FieldFile open.
        candidate_pks: list[int] = []
        for product in products.iterator(chunk_size=50):
            if product_image_needs_processing(product):
                candidate_pks.append(product.pk)
            else:
                skipped += 1
            image_field = getattr(product, "image", None)
            if image_field is not None and hasattr(image_field, "close"):
                try:
                    image_field.close()
                except Exception:
                    pass

        self.stdout.write(f"Products with images: {total_with_images}")
        self.stdout.write(f"Already processed (skip): {skipped}")
        self.stdout.write(f"Candidates to process: {len(candidate_pks)}")

        processed = 0
        errors = 0
        skipped_concurrent = 0
        # F11: only count bytes for the same successful set.
        bytes_before_success = 0
        bytes_after = 0
        for pk in candidate_pks:
            product = Product.objects.get(pk=pk)
            before = field_file_size(product.image) + field_file_size(product.image_thumb)
            expected_name = product.image.name if product.image else ""
            try:
                result = process_and_save_product_image(
                    product,
                    expected_image_name=expected_name,
                    bump_updated_at=False,
                )
                if result is None:
                    skipped_concurrent += 1
                    self.stdout.write(
                        f"  skipped product pk={product.pk} "
                        f"(image changed since candidate load)"
                    )
                    continue
                product.refresh_from_db()
                bytes_before_success += before
                bytes_after += field_file_size(product.image)
                bytes_after += field_file_size(product.image_thumb)
                processed += 1
                self.stdout.write(f"  processed product pk={product.pk} ({product.product_code})")
            except ProductImageError as exc:
                errors += 1
                self.stderr.write(f"  FAILED product pk={product.pk}: {exc}")
            finally:
                image_field = getattr(product, "image", None)
                if image_field is not None and hasattr(image_field, "close"):
                    try:
                        image_field.close()
                    except Exception:
                        pass

        self.stdout.write(f"Processed: {processed}")
        self.stdout.write(f"Skipped (concurrent edit): {skipped_concurrent}")
        self.stdout.write(f"Errors: {errors}")
        self.stdout.write(f"Bytes before (successes only): {bytes_before_success}")
        self.stdout.write(f"Bytes after: {bytes_after}")
        if bytes_before_success:
            saved = bytes_before_success - bytes_after
            pct = (saved / bytes_before_success) * 100
            self.stdout.write(f"Bytes saved: {saved} ({pct:.1f}%)")

        if errors:
            # Do not report success when images failed. An operator running this
            # over a whole catalogue must not see green text while photos were
            # skipped, because the run is irreversible for everything that did
            # succeed and the failures need attention before a re-run.
            raise CommandError(
                f"Backfill finished with {errors} failed image(s) out of "
                f"{len(candidate_pks)} candidate(s). Review the FAILED lines above. "
                f"Successfully processed images have already been replaced."
            )
        self.stdout.write(self.style.SUCCESS("Backfill complete."))
