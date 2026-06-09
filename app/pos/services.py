from dataclasses import dataclass
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from audit.models import AuditLog
from audit.services import create_audit_log
from catalog.models import Product
from core.permissions import is_admin_user
from inventory.models import InventoryMovement, StockBatch

from .models import Sale, SaleItem
from .pricing import allocate_discount, choose_best_promotion, get_cost_snapshot, money


@dataclass(frozen=True)
class ParsedCustomCode:
    original_barcode: str
    indicator: str
    expiry_yymmdd: str
    batch_no: str


def parse_custom_code(scan_value):
    parts = scan_value.strip().split("-")
    if len(parts) != 4:
        raise ValidationError("Invalid Melodu custom code format.")

    original_barcode, indicator, expiry_yymmdd, batch_no = parts
    if indicator != "M":
        raise ValidationError("Invalid Melodu code indicator.")
    if len(expiry_yymmdd) != 6 or not expiry_yymmdd.isdigit():
        raise ValidationError("Invalid expiry date in custom code.")
    if not batch_no.startswith("B"):
        raise ValidationError("Invalid batch number in custom code.")

    return ParsedCustomCode(
        original_barcode=original_barcode,
        indicator=indicator,
        expiry_yymmdd=expiry_yymmdd,
        batch_no=batch_no,
    )


def is_custom_code(scan_value):
    try:
        parse_custom_code(scan_value)
    except ValidationError:
        return False
    return True


def validate_sellable_batch(stock_batch, quantity=1):
    if not stock_batch.product.is_active:
        raise ValidationError("Inactive product cannot be sold.")
    if stock_batch.status != StockBatch.Status.ACTIVE:
        raise ValidationError("Stock batch is not active.")
    if stock_batch.expiry_date < timezone.localdate():
        raise ValidationError("Expired stock cannot be sold.")
    if stock_batch.quantity_available < quantity:
        raise ValidationError("Not enough stock available.")


def lookup_original_barcode(original_barcode):
    try:
        product = Product.objects.get(original_barcode=original_barcode)
    except Product.DoesNotExist as exc:
        raise ValidationError("Original barcode does not exist.") from exc

    if not product.is_active:
        raise ValidationError("Inactive product cannot be sold.")

    batches = (
        StockBatch.objects.select_related("product", "supplier")
        .filter(
            product=product,
            status=StockBatch.Status.ACTIVE,
            quantity_available__gt=0,
            expiry_date__gte=timezone.localdate(),
        )
        .order_by("expiry_date", "batch_no")
    )

    return {
        "scan_type": "ORIGINAL_BARCODE",
        "product": product,
        "available_batches": list(batches),
        "requires_batch_selection": True,
    }


def lookup_custom_code(custom_code):
    parsed = parse_custom_code(custom_code)
    try:
        product = Product.objects.get(original_barcode=parsed.original_barcode)
    except Product.DoesNotExist as exc:
        raise ValidationError("Original barcode does not exist.") from exc

    try:
        stock_batch = StockBatch.objects.select_related("product", "supplier").get(batch_no=parsed.batch_no)
    except StockBatch.DoesNotExist as exc:
        raise ValidationError("Batch number does not exist.") from exc

    if stock_batch.product_id != product.id:
        raise ValidationError("Product and batch do not match.")
    if stock_batch.expiry_date.strftime("%y%m%d") != parsed.expiry_yymmdd:
        raise ValidationError("Expiry date does not match stock batch.")
    validate_sellable_batch(stock_batch)

    return {
        "scan_type": "CUSTOM_CODE",
        "product": product,
        "stock_batch": stock_batch,
        "requires_batch_selection": False,
    }


def scan_code(scan_value):
    scan_value = scan_value.strip()
    if not scan_value:
        raise ValidationError("Scan value is required.")
    if "-" in scan_value:
        return lookup_custom_code(scan_value)
    return lookup_original_barcode(scan_value)


def generate_sale_no(today=None):
    today = today or timezone.localdate()
    prefix = f"S{today:%y%m%d}"
    latest = (
        Sale.objects.select_for_update()
        .filter(sale_no__startswith=prefix)
        .order_by("-sale_no")
        .first()
    )
    next_number = 1
    if latest:
        next_number = int(latest.sale_no[-4:]) + 1
    return f"{prefix}{next_number:04d}"


@transaction.atomic
def confirm_sale(
    *,
    cart_items,
    cashier,
    payment_method=Sale.PaymentMethod.CASH,
    discount_amount=Decimal("0.00"),
    override_reason="",
    request=None,
):
    if not cart_items:
        raise ValidationError("Cart is empty.")

    normalized_items = []
    batch_ids = [item["stock_batch"].id if isinstance(item["stock_batch"], StockBatch) else item["stock_batch"] for item in cart_items]
    locked_batches = {
        batch.id: batch
        for batch in StockBatch.objects.select_for_update()
        .select_related("product", "supplier")
        .filter(id__in=batch_ids)
    }

    total_amount = Decimal("0.00")
    for item in cart_items:
        stock_batch_id = item["stock_batch"].id if isinstance(item["stock_batch"], StockBatch) else item["stock_batch"]
        quantity = int(item["quantity"])
        if quantity <= 0:
            raise ValidationError("Sale quantity must be greater than zero.")
        stock_batch = locked_batches.get(stock_batch_id)
        if stock_batch is None:
            raise ValidationError("Stock batch does not exist.")
        validate_sellable_batch(stock_batch, quantity=quantity)
        cost_snapshot = get_cost_snapshot(stock_batch)
        promotion_price = choose_best_promotion(stock_batch)
        original_line_total = money(promotion_price.original_unit_price * quantity)
        promotion_line_total = money(promotion_price.final_unit_price * quantity)
        promotion_discount_total = money(promotion_price.discount_per_unit * quantity)
        total_amount += original_line_total
        normalized_items.append(
            {
                "stock_batch": stock_batch,
                "quantity": quantity,
                "cost_snapshot": cost_snapshot,
                "promotion_price": promotion_price,
                "original_line_total": original_line_total,
                "promotion_line_total": promotion_line_total,
                "promotion_discount_total": promotion_discount_total,
            }
        )

    discount_amount = money(discount_amount or "0.00")
    if discount_amount < 0:
        raise ValidationError("Discount cannot be negative.")
    promotion_discount_amount = sum((item["promotion_discount_total"] for item in normalized_items), Decimal("0.00"))
    pre_manual_total = sum((item["promotion_line_total"] for item in normalized_items), Decimal("0.00"))
    if discount_amount > pre_manual_total:
        raise ValidationError("Discount cannot exceed total amount.")

    manual_allocations = allocate_discount(
        discount_amount,
        [item["promotion_line_total"] for item in normalized_items],
    )
    below_cost_items = []
    for item, manual_discount in zip(normalized_items, manual_allocations):
        item["manual_discount_total"] = manual_discount
        item["line_discount_total"] = money(item["promotion_discount_total"] + manual_discount)
        item["final_line_total"] = money(item["promotion_line_total"] - manual_discount)
        item["final_unit_price"] = money(item["final_line_total"] / item["quantity"])
        item["below_cost"] = item["final_line_total"] < money(item["cost_snapshot"].cost_basis * item["quantity"])
        item["below_cost_allowed_by_promotion"] = bool(
            item["below_cost"]
            and item["promotion_price"].promotion
            and item["promotion_price"].promotion.allow_below_cost
            and manual_discount == 0
        )
        if item["below_cost"] and not item["below_cost_allowed_by_promotion"]:
            below_cost_items.append(item)

    override_reason = (override_reason or "").strip()
    override_user = None
    if below_cost_items:
        if not is_admin_user(cashier):
            raise ValidationError("Manager approval required for this price.")
        if not override_reason:
            raise ValidationError("Override reason is required for below-cost sale.")
        override_user = cashier

    final_amount = sum((item["final_line_total"] for item in normalized_items), Decimal("0.00"))

    sale = Sale.objects.create(
        sale_no=generate_sale_no(),
        cashier=cashier,
        total_amount=total_amount,
        discount_amount=money(promotion_discount_amount + discount_amount),
        final_amount=money(final_amount),
        payment_method=payment_method,
        status=Sale.Status.COMPLETED,
    )

    for item in normalized_items:
        stock_batch = item["stock_batch"]
        quantity = item["quantity"]
        cost_snapshot = item["cost_snapshot"]
        promotion = item["promotion_price"].promotion
        SaleItem.objects.create(
            sale=sale,
            product=stock_batch.product,
            stock_batch=stock_batch,
            quantity=quantity,
            unit_price=item["promotion_price"].original_unit_price,
            reference_cost_at_sale=cost_snapshot.reference_unit_cost,
            actual_cost_at_sale=cost_snapshot.actual_unit_cost,
            landed_cost_at_sale=cost_snapshot.landed_unit_cost,
            cost_basis_at_sale=cost_snapshot.cost_basis,
            original_unit_price=item["promotion_price"].original_unit_price,
            final_unit_price=item["final_unit_price"],
            discount_amount=item["line_discount_total"],
            promotion=promotion,
            promotion_name_at_sale=promotion.name if promotion else "",
            override_by=override_user if item["below_cost"] and not item["below_cost_allowed_by_promotion"] else None,
            override_reason=override_reason if item["below_cost"] and not item["below_cost_allowed_by_promotion"] else "",
            subtotal=item["final_line_total"],
        )
        stock_batch.quantity_available -= quantity
        if stock_batch.quantity_available == 0:
            stock_batch.status = StockBatch.Status.SOLD_OUT
        stock_batch.full_clean()
        stock_batch.save(update_fields=["quantity_available", "status", "updated_at"])
        InventoryMovement.objects.create(
            product=stock_batch.product,
            stock_batch=stock_batch,
            movement_type=InventoryMovement.MovementType.SALE,
            quantity=quantity,
            reference_type="Sale",
            reference_id=str(sale.pk),
            note=f"Sale {sale.sale_no}",
            created_by=cashier,
        )

    below_cost_payload = [
        {
            "product": item["stock_batch"].product.product_code,
            "stock_batch": item["stock_batch"].batch_no,
            "reference_cost": str(item["cost_snapshot"].reference_unit_cost),
            "actual_cost": str(item["cost_snapshot"].actual_unit_cost),
            "landed_cost": str(item["cost_snapshot"].landed_unit_cost)
            if item["cost_snapshot"].landed_unit_cost is not None
            else None,
            "cost_basis": str(item["cost_snapshot"].cost_basis),
            "final_unit_price": str(item["final_unit_price"]),
            "promotion": item["promotion_price"].promotion_name,
            "override_user": override_user.username if override_user else "",
            "override_reason": override_reason if override_user else "",
        }
        for item in normalized_items
        if item["below_cost"]
    ]
    if below_cost_payload:
        create_audit_log(
            action=AuditLog.Action.BELOW_COST_SALE,
            module="pos",
            user=cashier,
            request=request,
            object_type="Sale",
            object_id=sale.pk,
            object_display=sale.sale_no,
            new_value={"items": below_cost_payload},
        )
    if override_user:
        create_audit_log(
            action=AuditLog.Action.SALE_OVERRIDE,
            module="pos",
            user=override_user,
            request=request,
            object_type="Sale",
            object_id=sale.pk,
            object_display=sale.sale_no,
            new_value={"reason": override_reason, "items": below_cost_payload},
        )
    promotion_below_cost_payload = [
        item
        for item in below_cost_payload
        if item["promotion"] and not item["override_user"]
    ]
    if promotion_below_cost_payload:
        create_audit_log(
            action=AuditLog.Action.PROMOTION_BELOW_COST_SALE,
            module="pos",
            user=cashier,
            request=request,
            object_type="Sale",
            object_id=sale.pk,
            object_display=sale.sale_no,
            new_value={"items": promotion_below_cost_payload},
        )

    create_audit_log(
        action=AuditLog.Action.SALE_CREATE,
        module="pos",
        user=cashier,
        request=request,
        object_type="Sale",
        object_id=sale.pk,
        object_display=sale.sale_no,
        new_value={
            "sale_no": sale.sale_no,
            "total_amount": str(sale.total_amount),
            "discount_amount": str(sale.discount_amount),
            "final_amount": str(sale.final_amount),
            "payment_method": sale.payment_method,
            "items": sale.items.aggregate(total_quantity=Sum("quantity"))["total_quantity"],
            "below_cost_items": len(below_cost_payload),
        },
    )

    return sale


@transaction.atomic
def cancel_sale(*, sale, cancelled_by, reason, request=None):
    if not reason or not reason.strip():
        raise ValidationError("Cancellation reason is required.")

    sale = Sale.objects.select_for_update().get(pk=sale.pk)
    if sale.status != Sale.Status.COMPLETED:
        raise ValidationError("Only completed sales can be cancelled.")

    items = list(sale.items.select_related("stock_batch", "product"))
    batch_ids = [item.stock_batch_id for item in items]
    locked_batches = {
        batch.id: batch
        for batch in StockBatch.objects.select_for_update().filter(id__in=batch_ids)
    }

    for item in items:
        stock_batch = locked_batches[item.stock_batch_id]
        stock_batch.quantity_available += item.quantity
        if stock_batch.expiry_date < timezone.localdate():
            stock_batch.status = StockBatch.Status.EXPIRED
        elif stock_batch.status == StockBatch.Status.SOLD_OUT:
            stock_batch.status = StockBatch.Status.ACTIVE
        stock_batch.full_clean()
        stock_batch.save(update_fields=["quantity_available", "status", "updated_at"])
        InventoryMovement.objects.create(
            product=item.product,
            stock_batch=stock_batch,
            movement_type=InventoryMovement.MovementType.RETURN,
            quantity=item.quantity,
            reference_type="Sale",
            reference_id=str(sale.pk),
            note=f"Cancellation of {sale.sale_no}: {reason.strip()}",
            created_by=cancelled_by,
        )

    sale.status = Sale.Status.CANCELLED
    sale.cancel_reason = reason.strip()
    sale.save(update_fields=["status", "cancel_reason", "updated_at"])

    create_audit_log(
        action=AuditLog.Action.SALE_CANCEL,
        module="pos",
        user=cancelled_by,
        request=request,
        object_type="Sale",
        object_id=sale.pk,
        object_display=sale.sale_no,
        old_value={"status": Sale.Status.COMPLETED},
        new_value={"status": Sale.Status.CANCELLED, "reason": sale.cancel_reason},
    )

    return sale
