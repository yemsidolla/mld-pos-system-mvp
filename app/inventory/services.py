from decimal import Decimal
from io import BytesIO

import barcode
import qrcode
from barcode.writer import ImageWriter
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.db import transaction
from django.utils import timezone

from audit.models import AuditLog
from audit.services import create_audit_log

from .models import InventoryMovement, StockBatch


def generate_batch_number(today=None):
    today = today or timezone.localdate()
    year_suffix = today.strftime("%y")
    prefix = f"B{year_suffix}"
    latest = (
        StockBatch.objects.select_for_update()
        .filter(batch_no__startswith=prefix)
        .order_by("-batch_no")
        .first()
    )
    next_number = 1
    if latest:
        next_number = int(latest.batch_no[-4:]) + 1
    return f"{prefix}{next_number:04d}"


def build_custom_code(product, expiry_date, batch_no):
    if not product.original_barcode:
        raise ValidationError("Product must have an original barcode before stock-in.")
    return f"{product.original_barcode}-M-{expiry_date:%y%m%d}-{batch_no}"


def generate_barcode_file(custom_code):
    code128 = barcode.get_barcode_class("code128")
    buffer = BytesIO()
    code128(custom_code, writer=ImageWriter()).write(
        buffer,
        options={
            "module_height": 12,
            "font_size": 8,
            "quiet_zone": 2,
            "write_text": True,
        },
    )
    return ContentFile(buffer.getvalue(), name=f"{custom_code}.png")


def generate_qr_file(custom_code):
    image = qrcode.make(custom_code)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return ContentFile(buffer.getvalue(), name=f"{custom_code}.png")


@transaction.atomic
def receive_stock(
    *,
    product,
    supplier,
    quantity,
    expiry_date,
    cost_price,
    selling_price,
    received_by,
    request=None,
    note="",
):
    if quantity <= 0:
        raise ValidationError("Quantity must be greater than zero.")
    if not product.is_active:
        raise ValidationError("Inactive product cannot receive stock.")
    if not supplier.is_active:
        raise ValidationError("Inactive supplier cannot be used for stock-in.")
    if expiry_date is None:
        raise ValidationError("Expiry date is required.")

    batch_no = generate_batch_number()
    custom_code = build_custom_code(product, expiry_date, batch_no)
    stock_batch = StockBatch(
        product=product,
        supplier=supplier,
        batch_no=batch_no,
        expiry_date=expiry_date,
        quantity_received=quantity,
        quantity_available=quantity,
        cost_price=Decimal(cost_price),
        selling_price=Decimal(selling_price),
        custom_code=custom_code,
        received_by=received_by,
    )
    stock_batch.full_clean()
    stock_batch.save()
    stock_batch.barcode_image.save(f"{custom_code}.png", generate_barcode_file(custom_code), save=False)
    stock_batch.qr_image.save(f"{custom_code}.png", generate_qr_file(custom_code), save=False)
    stock_batch.save(update_fields=["barcode_image", "qr_image", "updated_at"])

    movement = InventoryMovement.objects.create(
        product=product,
        stock_batch=stock_batch,
        movement_type=InventoryMovement.MovementType.STOCK_IN,
        quantity=quantity,
        reference_type="StockBatch",
        reference_id=str(stock_batch.pk),
        note=note,
        created_by=received_by,
    )

    create_audit_log(
        action=AuditLog.Action.STOCK_IN,
        module="inventory",
        user=received_by,
        request=request,
        object_type="StockBatch",
        object_id=stock_batch.pk,
        object_display=stock_batch.batch_no,
        new_value={
            "product": product.product_code,
            "supplier": supplier.name,
            "quantity": quantity,
            "expiry_date": expiry_date.isoformat(),
            "custom_code": custom_code,
        },
    )

    return stock_batch, movement


def get_expiry_status(stock_batch, today=None):
    today = today or timezone.localdate()
    days_until_expiry = (stock_batch.expiry_date - today).days
    if days_until_expiry < 0:
        return "Expired"
    if days_until_expiry <= 30:
        return "Critical"
    if days_until_expiry <= 60:
        return "Warning"
    return "Normal"


def _refresh_status_for_quantity(stock_batch):
    if stock_batch.expiry_date < timezone.localdate():
        stock_batch.status = StockBatch.Status.EXPIRED
    elif stock_batch.quantity_available == 0:
        stock_batch.status = StockBatch.Status.SOLD_OUT
    elif stock_batch.status in {StockBatch.Status.SOLD_OUT, StockBatch.Status.EXPIRED}:
        stock_batch.status = StockBatch.Status.ACTIVE


@transaction.atomic
def adjust_stock(*, stock_batch, delta_quantity, reason, adjusted_by, request=None):
    if not reason or not reason.strip():
        raise ValidationError("Adjustment reason is required.")
    if delta_quantity == 0:
        raise ValidationError("Adjustment quantity cannot be zero.")

    stock_batch = StockBatch.objects.select_for_update().select_related("product").get(pk=stock_batch.pk)
    old_quantity = stock_batch.quantity_available
    new_quantity = old_quantity + delta_quantity
    if new_quantity < 0:
        raise ValidationError("Stock quantity cannot become negative.")
    stock_batch.quantity_available = new_quantity
    _refresh_status_for_quantity(stock_batch)
    stock_batch.full_clean()
    stock_batch.save(update_fields=["quantity_available", "status", "updated_at"])

    movement = InventoryMovement.objects.create(
        product=stock_batch.product,
        stock_batch=stock_batch,
        movement_type=InventoryMovement.MovementType.ADJUSTMENT,
        quantity=abs(delta_quantity),
        reference_type="StockBatch",
        reference_id=str(stock_batch.pk),
        note=reason.strip(),
        created_by=adjusted_by,
    )
    create_audit_log(
        action=AuditLog.Action.STOCK_ADJUSTMENT,
        module="inventory",
        user=adjusted_by,
        request=request,
        object_type="StockBatch",
        object_id=stock_batch.pk,
        object_display=stock_batch.batch_no,
        old_value={"quantity_available": old_quantity},
        new_value={"quantity_available": stock_batch.quantity_available, "reason": reason.strip()},
    )
    return stock_batch, movement


@transaction.atomic
def mark_batch_damaged(*, stock_batch, quantity, reason, marked_by, request=None):
    if not reason or not reason.strip():
        raise ValidationError("Damage reason is required.")
    if quantity <= 0:
        raise ValidationError("Damage quantity must be greater than zero.")

    stock_batch = StockBatch.objects.select_for_update().select_related("product").get(pk=stock_batch.pk)
    if quantity > stock_batch.quantity_available:
        raise ValidationError("Stock quantity cannot become negative.")
    old_quantity = stock_batch.quantity_available
    stock_batch.quantity_available -= quantity
    if stock_batch.quantity_available == 0:
        stock_batch.status = StockBatch.Status.DAMAGED
    stock_batch.full_clean()
    stock_batch.save(update_fields=["quantity_available", "status", "updated_at"])

    movement = InventoryMovement.objects.create(
        product=stock_batch.product,
        stock_batch=stock_batch,
        movement_type=InventoryMovement.MovementType.DAMAGE,
        quantity=quantity,
        reference_type="StockBatch",
        reference_id=str(stock_batch.pk),
        note=reason.strip(),
        created_by=marked_by,
    )
    create_audit_log(
        action=AuditLog.Action.STOCK_ADJUSTMENT,
        module="inventory",
        user=marked_by,
        request=request,
        object_type="StockBatch",
        object_id=stock_batch.pk,
        object_display=stock_batch.batch_no,
        old_value={"quantity_available": old_quantity},
        new_value={"quantity_available": stock_batch.quantity_available, "status": stock_batch.status, "reason": reason.strip()},
    )
    return stock_batch, movement


@transaction.atomic
def mark_batch_expired(*, stock_batch, reason, marked_by, request=None):
    if not reason or not reason.strip():
        raise ValidationError("Expired stock reason is required.")

    stock_batch = StockBatch.objects.select_for_update().select_related("product").get(pk=stock_batch.pk)
    old_quantity = stock_batch.quantity_available
    old_status = stock_batch.status
    if old_quantity <= 0:
        raise ValidationError("No available stock to mark as expired.")

    stock_batch.quantity_available = 0
    stock_batch.status = StockBatch.Status.EXPIRED
    stock_batch.full_clean()
    stock_batch.save(update_fields=["quantity_available", "status", "updated_at"])

    movement = InventoryMovement.objects.create(
        product=stock_batch.product,
        stock_batch=stock_batch,
        movement_type=InventoryMovement.MovementType.EXPIRED,
        quantity=old_quantity,
        reference_type="StockBatch",
        reference_id=str(stock_batch.pk),
        note=reason.strip(),
        created_by=marked_by,
    )
    create_audit_log(
        action=AuditLog.Action.STOCK_ADJUSTMENT,
        module="inventory",
        user=marked_by,
        request=request,
        object_type="StockBatch",
        object_id=stock_batch.pk,
        object_display=stock_batch.batch_no,
        old_value={"quantity_available": old_quantity, "status": old_status},
        new_value={"quantity_available": 0, "status": StockBatch.Status.EXPIRED, "reason": reason.strip()},
    )
    return stock_batch, movement
