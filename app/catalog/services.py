"""Catalog business services.

Product photo processing lives here (not in views/templates). Scope is
``Product.image`` / ``Product.image_thumb`` only — never barcode, QR, KHQR, or logo.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from io import BytesIO

from django.core.files.base import ContentFile
from PIL import Image, ImageOps, UnidentifiedImageError

ORIGINAL_MAX_EDGE = 1600
THUMB_MAX_EDGE = 96
ORIGINAL_WEBP_QUALITY = 82
THUMB_WEBP_QUALITY = 80


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
    except OSError as exc:
        raise ProductImageError("Could not read the uploaded image. Please upload a valid photo.") from exc


def _to_webp_compatible(image: Image.Image) -> Image.Image:
    """Apply EXIF orientation, then convert to a WebP-safe mode without EXIF."""
    image = ImageOps.exif_transpose(image)

    if image.mode in ("RGBA", "LA"):
        converted = image.convert("RGBA")
    elif image.mode == "P":
        if "transparency" in image.info:
            converted = image.convert("RGBA")
        else:
            converted = image.convert("RGB")
    elif image.mode == "CMYK":
        converted = image.convert("RGB")
    elif image.mode == "L":
        converted = image.convert("RGB")
    elif image.mode == "RGB":
        converted = image.copy()
    else:
        converted = image.convert("RGB")

    # Fresh image so GPS/EXIF and other metadata are not carried into the encoder.
    clean = Image.new(converted.mode, converted.size)
    clean.putdata(list(converted.getdata()))
    return clean


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
    original_image = _fit_long_edge(image, ORIGINAL_MAX_EDGE)
    thumb_image = _fit_long_edge(image, THUMB_MAX_EDGE)

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
    product.image.save(processed.original_name, processed.original, save=False)
    product.image_thumb.save(processed.thumb_name, processed.thumb, save=False)


def clear_product_images(product) -> None:
    """Clear both product photo fields (no DB save)."""
    if product.image:
        product.image.delete(save=False)
    if product.image_thumb:
        product.image_thumb.delete(save=False)
    product.image = None
    product.image_thumb = None


def product_image_needs_processing(product) -> bool:
    """Return True when backfill should rewrite this product's photo."""
    if not product.image:
        return False
    if not product.image_thumb:
        return True
    # Already has a thumb from a prior run — treat as processed (idempotent skip).
    name = (product.image.name or "").lower()
    return not name.endswith(".webp")


def process_and_save_product_image(product, source=None, *, source_name: str | None = None) -> ProcessedProductImages:
    """Process ``source`` (or the product's current image) and save both fields."""
    file_obj = source if source is not None else product.image
    if not file_obj:
        raise ProductImageError("No product image to process.")
    name = source_name or getattr(file_obj, "name", None)
    processed = process_product_image(file_obj, source_name=name)
    # Replace stored original in place: delete old files after assigning new ones
    # only when names differ; ImageField.save handles storage write.
    old_image_name = product.image.name if product.image else ""
    old_thumb_name = product.image_thumb.name if product.image_thumb else ""
    assign_product_images(product, processed)
    product.save(update_fields=["image", "image_thumb", "updated_at"])
    # Best-effort cleanup of replaced objects (ignore missing).
    storage = product.image.storage
    for old_name in (old_image_name, old_thumb_name):
        if old_name and old_name != product.image.name and old_name != (product.image_thumb.name if product.image_thumb else ""):
            try:
                if storage.exists(old_name):
                    storage.delete(old_name)
            except Exception:
                pass
    return processed


def field_file_size(field_file) -> int:
    """Return stored byte size, or 0 when unavailable."""
    if not field_file:
        return 0
    try:
        return int(field_file.size)
    except Exception:
        return 0
