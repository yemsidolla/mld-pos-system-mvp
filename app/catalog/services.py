"""Catalog business services.

Product photo processing lives here (not in views/templates). Scope is
``Product.image`` / ``Product.image_thumb`` only — never barcode, QR, KHQR, or logo.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from io import BytesIO

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db.models import Q
from PIL import Image, ImageOps, UnidentifiedImageError

ORIGINAL_MAX_EDGE = 1600
THUMB_MAX_EDGE = 96
ORIGINAL_WEBP_QUALITY = 82
THUMB_WEBP_QUALITY = 80

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
        return image
    except UnidentifiedImageError as exc:
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
    try:
        product.image.save(processed.original_name, processed.original, save=False)
        product.image_thumb.save(processed.thumb_name, processed.thumb, save=False)
    except _STORAGE_ERRORS as exc:
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
    return (name or "").replace("\\", "/").lstrip("/")


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
    """True when another Product row still points at this storage key."""
    from catalog.models import Product

    key = _normalized_storage_key(name)
    if not key:
        return False
    qs = Product.objects.filter(Q(image=key) | Q(image_thumb=key))
    if exclude_pk is not None:
        qs = qs.exclude(pk=exclude_pk)
    return qs.exists()


def safe_delete_product_image_key(storage, name: str, *, exclude_product_pk=None) -> None:
    """Delete a storage key only when it is a product-image path and unreferenced.

    Refuses keys outside ``products/`` (including barcodes/, qrcodes/, store/).
    Logs deletion failures instead of swallowing them silently.
    """
    key = _normalized_storage_key(name)
    if not key:
        return
    if not is_safe_product_image_key(key):
        logger.warning("Refusing to delete non-product-image storage key: %s", key)
        return
    if product_image_key_still_referenced(key, exclude_pk=exclude_product_pk):
        logger.info("Skipping delete; storage key still referenced by another product: %s", key)
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

        # Write-then-delete: only after DB save succeeded.
        cleanup_replaced_product_image_keys(
            (old_image_name, old_thumb_name),
            product=locked,
            current_image_name=locked.image.name if locked.image else "",
            current_thumb_name=locked.image_thumb.name if locked.image_thumb else "",
        )

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
