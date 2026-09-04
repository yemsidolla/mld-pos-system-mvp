"""Catalog business services.

Product photo processing lives here (not in views/templates). Scope is
``Product.image`` / ``Product.image_thumb`` only — never barcode, QR, KHQR, or logo.
"""

from __future__ import annotations

import logging
import os
import posixpath
from dataclasses import dataclass
from io import BytesIO

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from PIL import Image, ImageOps, UnidentifiedImageError

try:  # pragma: no cover - depends on the wheel being installed
    # Registers HEIC/HEIF with Pillow so Image.open() handles iPhone photos.
    # Imported defensively: if the wheel is missing on some platform the app
    # must still start, and HEIC simply stays unsupported rather than taking
    # every image path down with an ImportError at startup.
    from pillow_heif import register_heif_opener

    register_heif_opener()
    HEIF_SUPPORTED = True
except Exception:  # pragma: no cover
    HEIF_SUPPORTED = False

ORIGINAL_MAX_EDGE = 1600
# 320, not the original 96: this one derivative now serves BOTH the 46px
# table thumbnail (downscaled, still crisp) and the V8 card grid, which
# renders it into a ~175-215px box. At 96px that box was a 2-4x upscale and
# visibly soft, worst on the phones staff actually use. A second stored size
# was considered and rejected — the model, the write/cleanup/backfill
# pipeline, and the templates all treat "the small derivative" as singular,
# and one right-sized image serves both call sites without adding a field.
THUMB_MAX_EDGE = 320
ORIGINAL_WEBP_QUALITY = 82
THUMB_WEBP_QUALITY = 82  # was 80; bumped to match ORIGINAL now that this
# derivative is displayed near 1:1 rather than always shrunk further.

# Only keys under these prefixes may be deleted by product-image cleanup.
# Never delete barcodes/, qrcodes/, store/, or any other media tree.
_PRODUCT_IMAGE_PREFIXES = ("products/",)

logger = logging.getLogger(__name__)

try:
    from botocore.exceptions import BotoCoreError, ClientError

    _STORAGE_ERRORS: tuple[type[BaseException], ...] = (BotoCoreError, ClientError, OSError)
except ImportError:  # pragma: no cover - botocore optional when USE_S3_MEDIA=False
    _STORAGE_ERRORS = (OSError,)


class ProductImageError(Exception):
    """Raised when a product photo cannot be read or encoded."""


@dataclass(frozen=True)
class ProcessedProductImages:
    """WebP derivatives ready to assign to a Product."""

    original: ContentFile
    thumb: ContentFile
    original_name: str
    thumb_name: str


def _webp_stem(source_name: str) -> str:
    base = os.path.basename(source_name or "image")
    stem, _ext = os.path.splitext(base)
    stem = (stem or "image").strip() or "image"
    return stem


def _open_image(source) -> Image.Image:
    try:
        if hasattr(source, "open"):
            try:
                source.open("rb")
            except Exception:
                pass
        if hasattr(source, "seek"):
            try:
                source.seek(0)
            except Exception:
                pass
        image = Image.open(source)
        image.load()
        # Pixels are in memory after load(); close the underlying handle so
        # dry-run / backfill over a large catalogue cannot exhaust FDs (R6).
        if hasattr(source, "close"):
            try:
                source.close()
            except Exception:
                pass
        return image
    except UnidentifiedImageError as exc:
        # Say WHAT was wrong. "Please upload a valid photo" is useless to
        # someone holding a perfectly good iPhone picture.
        name = (getattr(source, "name", "") or "").lower()
        if name.endswith((".heic", ".heif")) and not HEIF_SUPPORTED:
            raise ProductImageError(
                "HEIC photos are not supported on this server yet. On iPhone, "
                "either change Settings > Camera > Formats to Most Compatible, "
                "or share the photo (which converts it to JPEG) and upload that."
            ) from exc
        raise ProductImageError("Could not read the uploaded image. Please upload a valid photo.") from exc
    except Image.DecompressionBombError as exc:
        raise ProductImageError("Could not read the uploaded image. Please upload a valid photo.") from exc
    except _STORAGE_ERRORS as exc:
        raise ProductImageError("Could not read the uploaded image. Please upload a valid photo.") from exc


def _to_webp_compatible(image: Image.Image) -> Image.Image:
    """Apply EXIF orientation, then convert to a WebP-safe mode."""
    image = ImageOps.exif_transpose(image)

    if image.mode in ("RGBA", "LA"):
        return image.convert("RGBA")
    if image.mode == "P":
        if "transparency" in image.info:
            return image.convert("RGBA")
        return image.convert("RGB")
    if image.mode == "CMYK":
        return image.convert("RGB")
    if image.mode == "L":
        return image.convert("RGB")
    if image.mode == "RGB":
        return image
    return image.convert("RGB")


def _strip_metadata(image: Image.Image) -> Image.Image:
    """Drop EXIF/GPS and other ancillary metadata cheaply.

    Rebuild from raw bytes after resize so any copy is of the small image.
    Never materialise a per-pixel Python list (``getdata`` / ``putdata``).
    Saving without ``exif=`` already omits EXIF; this also clears ``info``.
    """
    return Image.frombytes(image.mode, image.size, image.tobytes())


def _fit_long_edge(image: Image.Image, max_edge: int) -> Image.Image:
    width, height = image.size
    long_edge = max(width, height)
    if long_edge <= max_edge:
        return image
    scale = max_edge / float(long_edge)
    new_size = (max(1, round(width * scale)), max(1, round(height * scale)))
    return image.resize(new_size, Image.Resampling.LANCZOS)


def _encode_webp(image: Image.Image, *, quality: int) -> bytes:
    buffer = BytesIO()
    # Do not pass exif= — metadata must not land in the WebP output.
    image.save(buffer, format="WEBP", quality=quality, method=4)
    return buffer.getvalue()


def process_product_image(source, *, source_name: str | None = None) -> ProcessedProductImages:
    """Build capped original + thumbnail WebP files from an upload or stored file.

    Never upscales. Applies EXIF orientation before resize. Strips EXIF from output.
    """
    name = source_name or getattr(source, "name", None) or "image"
    stem = _webp_stem(name)
    original_name = f"{stem}.webp"
    thumb_name = f"{stem}.webp"

    image = _to_webp_compatible(_open_image(source))
    # Resize first, then strip metadata on the smaller buffers (F5).
    original_image = _strip_metadata(_fit_long_edge(image, ORIGINAL_MAX_EDGE))
    thumb_image = _strip_metadata(_fit_long_edge(image, THUMB_MAX_EDGE))

    try:
        original_bytes = _encode_webp(original_image, quality=ORIGINAL_WEBP_QUALITY)
        thumb_bytes = _encode_webp(thumb_image, quality=THUMB_WEBP_QUALITY)
    except OSError as exc:
        raise ProductImageError("Could not encode the uploaded image. Please try another photo.") from exc

    return ProcessedProductImages(
        original=ContentFile(original_bytes, name=original_name),
        thumb=ContentFile(thumb_bytes, name=thumb_name),
        original_name=original_name,
        thumb_name=thumb_name,
    )


def assign_product_images(product, processed: ProcessedProductImages) -> None:
    """Assign processed files to ``product.image`` and ``product.image_thumb`` (no DB save)."""
    previous_image_name = product.image.name if product.image else ""
    new_original_name = ""
    try:
        product.image.save(processed.original_name, processed.original, save=False)
        new_original_name = product.image.name if product.image else ""
        product.image_thumb.save(processed.thumb_name, processed.thumb, save=False)
    except _STORAGE_ERRORS as exc:
        # Original is written before thumb — delete the orphan on thumb failure (R5).
        if new_original_name and new_original_name != previous_image_name:
            try:
                storage = product.image.storage if product.image is not None else default_storage
                if storage.exists(new_original_name):
                    storage.delete(new_original_name)
            except Exception:
                logger.exception(
                    "Failed to clean up orphaned product original after thumb write failure: %s",
                    new_original_name,
                )
            # Restore prior field name so the in-memory instance is not left
            # pointing at a file we just deleted.
            if previous_image_name:
                product.image.name = previous_image_name
            else:
                product.image = None
        raise ProductImageError("Could not store the uploaded image. Please try again.") from exc


def clear_product_image_fields(product) -> None:
    """Null both product photo fields without deleting storage or saving the DB.

    Callers must save the row first, then delete old keys via
    ``safe_delete_product_image_key`` (write-then-delete ordering).
    """
    product.image = None
    product.image_thumb = None


# Backwards-compatible alias used by older call sites / tests.
def clear_product_images(product) -> None:
    """Clear image fields only (no storage delete, no DB save). Prefer ``clear_product_image_fields``."""
    clear_product_image_fields(product)


def _normalized_storage_key(name: str) -> str:
    """Return a canonical relative storage key, or ``""`` when the name is unsafe.

    Rejects absolute paths, empty/``.`` results, and any ``..`` segment (R1).
    Backslashes are treated as separators before canonicalisation so mixed
    separator traversal payloads cannot bypass the allow/deny lists.
    """
    raw = (name or "").replace("\\", "/")
    if not raw or raw.startswith("/"):
        return ""
    # Windows-style absolute (e.g. ``C:/...``) — never a valid relative media key.
    if len(raw) >= 2 and raw[1] == ":":
        return ""
    segments = raw.split("/")
    if any(seg == ".." for seg in segments):
        return ""
    if any(seg == "" for seg in segments):
        return ""
    if any(seg == "." for seg in segments):
        return ""
    canonical = posixpath.normpath(raw)
    if not canonical or canonical == "." or canonical.startswith("..") or canonical.startswith("/"):
        return ""
    if canonical != raw:
        # normpath must not invent a different path when we already forbade
        # ``..`` / ``.`` / empty segments — treat divergence as unsafe.
        return ""
    return canonical


def is_safe_product_image_key(name: str) -> bool:
    """Return True only for keys under product image prefixes (never barcodes/qrcodes/store)."""
    key = _normalized_storage_key(name)
    if not key:
        return False
    # Explicit denylist for known protected trees (defence in depth).
    for forbidden in ("barcodes/", "qrcodes/", "store/"):
        if key.startswith(forbidden):
            return False
    return any(key.startswith(prefix) for prefix in _PRODUCT_IMAGE_PREFIXES)


def product_image_key_still_referenced(name: str, *, exclude_pk=None) -> bool:
    """True when any media field still points at this storage key.

    Checks Product photos plus protected barcode / QR / logo / KHQR fields so a
    mis-pointed or traversal key cannot delete live protected media (R1).

    Product lookups are equality filters (not ``OR`` across the whole table in
    one expression) and only run for keys that already passed the product-image
    allowlist — backfill never scans protected trees.
    """
    key = _normalized_storage_key(name)
    if not key:
        return False

    from catalog.models import Product
    from core.models import StoreSetting
    from inventory.models import StockBatch

    # Protected media: any hit means "still referenced" (never delete).
    if (
        StockBatch.objects.filter(barcode_image=key).exists()
        or StockBatch.objects.filter(qr_image=key).exists()
        or StoreSetting.objects.filter(logo=key).exists()
        or StoreSetting.objects.filter(khqr_image=key).exists()
    ):
        return True

    # Bound the Product scan: only plausible product-image keys reach here
    # (caller already gated via is_safe_product_image_key). Two equality
    # lookups keep each check to a single column match.
    image_qs = Product.objects.filter(image=key)
    thumb_qs = Product.objects.filter(image_thumb=key)
    if exclude_pk is not None:
        image_qs = image_qs.exclude(pk=exclude_pk)
        thumb_qs = thumb_qs.exclude(pk=exclude_pk)
    return image_qs.exists() or thumb_qs.exists()


def safe_delete_product_image_key(storage, name: str, *, exclude_product_pk=None) -> None:
    """Delete a storage key only when it is a product-image path and unreferenced.

    Refuses keys outside ``products/`` (including barcodes/, qrcodes/, store/),
    absolute paths, and any traversal payload. Logs deletion failures instead of
    swallowing them silently.
    """
    key = _normalized_storage_key(name)
    if not key:
        logger.warning("Refusing to delete unsafe or empty storage key: %r", name)
        return
    if not is_safe_product_image_key(key):
        logger.warning("Refusing to delete non-product-image storage key: %s", key)
        return
    if product_image_key_still_referenced(key, exclude_pk=exclude_product_pk):
        logger.info("Skipping delete; storage key still referenced: %s", key)
        return
    try:
        if storage.exists(key):
            storage.delete(key)
    except Exception:
        logger.exception("Failed to delete product image storage key: %s", key)


def _product_image_storage(product=None):
    if product is not None and getattr(product, "image", None) is not None:
        try:
            return product.image.storage
        except Exception:
            pass
    from catalog.models import Product

    return Product._meta.get_field("image").storage or default_storage


def cleanup_replaced_product_image_keys(
    old_names,
    *,
    product,
    current_image_name: str = "",
    current_thumb_name: str = "",
) -> None:
    """Best-effort delete of previous original/thumb keys after a successful save."""
    storage = _product_image_storage(product)
    current = {_normalized_storage_key(current_image_name), _normalized_storage_key(current_thumb_name)}
    current.discard("")
    for old_name in old_names:
        key = _normalized_storage_key(old_name)
        if not key or key in current:
            continue
        safe_delete_product_image_key(storage, key, exclude_product_pk=getattr(product, "pk", None))


def product_image_needs_processing(product) -> bool:
    """Return True when backfill should rewrite this product's photo."""
    if not product.image:
        return False
    if not product.image_thumb:
        return True
    # Already has a thumb from a prior run — treat as processed (idempotent skip).
    name = (product.image.name or "").lower()
    return not name.endswith(".webp")


def process_and_save_product_image(
    product,
    source=None,
    *,
    source_name: str | None = None,
    expected_image_name: str | None = None,
    bump_updated_at: bool = False,
) -> ProcessedProductImages | None:
    """Process ``source`` (or the product's current image) and save both fields.

    When ``expected_image_name`` is set, re-reads the row under
    ``select_for_update`` and skips (returns None) if ``image.name`` changed —
    so a concurrent staff upload is not overwritten (F2).

    ``bump_updated_at`` defaults False so backfill does not rewrite catalogue
    timestamps (F10). Pass True for interactive paths that should touch
    ``updated_at``.

    Storage deletion of replaced keys is deferred with ``transaction.on_commit``
    so a failed commit cannot leave the row pointing at deleted files (R2).
    """
    from django.db import transaction

    from catalog.models import Product

    with transaction.atomic():
        locked = Product.objects.select_for_update().get(pk=product.pk)
        if expected_image_name is not None:
            current_name = locked.image.name if locked.image else ""
            if current_name != expected_image_name:
                logger.info(
                    "Skipping product pk=%s: image changed since candidate load (%r -> %r)",
                    locked.pk,
                    expected_image_name,
                    current_name,
                )
                return None

        file_obj = source if source is not None else locked.image
        if not file_obj:
            raise ProductImageError("No product image to process.")
        name = source_name or getattr(file_obj, "name", None)
        processed = process_product_image(file_obj, source_name=name)

        old_image_name = locked.image.name if locked.image else ""
        old_thumb_name = locked.image_thumb.name if locked.image_thumb else ""
        assign_product_images(locked, processed)

        update_fields = ["image", "image_thumb"]
        if bump_updated_at:
            update_fields.append("updated_at")
        try:
            locked.save(update_fields=update_fields)
        except _STORAGE_ERRORS as exc:
            raise ProductImageError("Could not store the uploaded image. Please try again.") from exc

        current_image_name = locked.image.name if locked.image else ""
        current_thumb_name = locked.image_thumb.name if locked.image_thumb else ""
        old_names = (old_image_name, old_thumb_name)
        product_pk = locked.pk

        def _cleanup_after_commit():
            # Re-load a thin product shell for storage resolution; names are captured.
            try:
                owner = Product.objects.get(pk=product_pk)
            except Product.DoesNotExist:
                owner = locked
            cleanup_replaced_product_image_keys(
                old_names,
                product=owner,
                current_image_name=current_image_name,
                current_thumb_name=current_thumb_name,
            )

        transaction.on_commit(_cleanup_after_commit)

        # Keep caller's in-memory instance roughly in sync.
        product.image = locked.image
        product.image_thumb = locked.image_thumb
        return processed


def field_file_size(field_file) -> int:
    """Return stored byte size, or 0 when unavailable."""
    if not field_file:
        return 0
    try:
        return int(field_file.size)
    except Exception:
        return 0
