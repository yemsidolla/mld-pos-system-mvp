from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render

from audit.models import AuditLog
from audit.services import create_audit_log
from catalog.models import Product
from core.permissions import inventory_required

from .forms import DamageStockForm, InventoryAdjustmentForm, LabelPrintForm, MarkExpiredForm, StockInForm
from .models import StockBatch
from .services import adjust_stock, get_expiry_status, mark_batch_damaged, mark_batch_expired, receive_stock


@inventory_required
def stock_in_view(request):
    form = StockInForm(request.POST or None)
    stock_batch = None

    if request.method == "POST" and form.is_valid():
        try:
            stock_batch, _movement = receive_stock(
                product=form.cleaned_data["product"],
                supplier=form.cleaned_data["supplier"],
                quantity=form.cleaned_data["quantity"],
                expiry_date=form.cleaned_data["expiry_date"],
                actual_unit_cost=form.cleaned_data["actual_unit_cost"],
                landed_unit_cost=form.cleaned_data["landed_unit_cost"],
                selling_price=form.cleaned_data["selling_price"],
                received_by=request.user,
                request=request,
                note=form.cleaned_data["note"],
            )
        except ValidationError as exc:
            form.add_error(None, exc)
        else:
            messages.success(request, f"Stock batch {stock_batch.batch_no} was created.")
            return redirect("stock-in")

    return render(request, "inventory/stock_in.html", {"form": form, "stock_batch": stock_batch})


@inventory_required
def barcode_print_view(request):
    form = LabelPrintForm(request.POST or None)
    stock_batch = None
    labels = []
    print_recorded = False

    if request.method == "POST" and form.is_valid():
        stock_batch = form.cleaned_data["stock_batch"]
        label_quantity = form.cleaned_data["label_quantity"]
        labels = range(label_quantity)

        if request.POST.get("action") == "print":
            create_audit_log(
                action=AuditLog.Action.BARCODE_PRINT,
                module="inventory",
                user=request.user,
                request=request,
                object_type="StockBatch",
                object_id=stock_batch.pk,
                object_display=stock_batch.batch_no,
                new_value={
                    "custom_code": stock_batch.custom_code,
                    "label_quantity": label_quantity,
                },
            )
            print_recorded = True
            messages.success(request, f"Print action recorded for {stock_batch.batch_no}.")

    return render(
        request,
        "inventory/barcode_print.html",
        {
            "form": form,
            "stock_batch": stock_batch,
            "labels": labels,
            "print_recorded": print_recorded,
        },
    )


@inventory_required
def inventory_summary_view(request):
    products = (
        Product.objects.filter(stock_batches__isnull=False)
        .annotate(total_available=Sum("stock_batches__quantity_available"))
        .order_by("name")
        .distinct()
    )
    batches = StockBatch.objects.select_related("product", "supplier").order_by("expiry_date", "batch_no")
    return render(request, "inventory/inventory_summary.html", {"products": products, "batches": batches})


@inventory_required
def stock_batch_detail_view(request, batch_id):
    stock_batch = get_object_or_404(StockBatch.objects.select_related("product", "supplier", "received_by"), pk=batch_id)
    adjustment_form = InventoryAdjustmentForm()
    damage_form = DamageStockForm()
    expired_form = MarkExpiredForm()

    if request.method == "POST":
        action = request.POST.get("action")
        try:
            if action == "adjust":
                adjustment_form = InventoryAdjustmentForm(request.POST)
                if adjustment_form.is_valid():
                    adjust_stock(
                        stock_batch=stock_batch,
                        delta_quantity=adjustment_form.cleaned_data["delta_quantity"],
                        reason=adjustment_form.cleaned_data["reason"],
                        adjusted_by=request.user,
                        request=request,
                    )
                    messages.success(request, "Stock adjustment recorded.")
                    return redirect("stock-batch-detail", batch_id=stock_batch.id)
            elif action == "damage":
                damage_form = DamageStockForm(request.POST)
                if damage_form.is_valid():
                    mark_batch_damaged(
                        stock_batch=stock_batch,
                        quantity=damage_form.cleaned_data["quantity"],
                        reason=damage_form.cleaned_data["reason"],
                        marked_by=request.user,
                        request=request,
                    )
                    messages.success(request, "Damaged stock recorded.")
                    return redirect("stock-batch-detail", batch_id=stock_batch.id)
            elif action == "expire":
                expired_form = MarkExpiredForm(request.POST)
                if expired_form.is_valid():
                    mark_batch_expired(
                        stock_batch=stock_batch,
                        reason=expired_form.cleaned_data["reason"],
                        marked_by=request.user,
                        request=request,
                    )
                    messages.success(request, "Expired stock recorded.")
                    return redirect("stock-batch-detail", batch_id=stock_batch.id)
        except ValidationError as exc:
            messages.error(request, "; ".join(exc.messages))

    stock_batch.refresh_from_db()
    return render(
        request,
        "inventory/stock_batch_detail.html",
        {
            "stock_batch": stock_batch,
            "expiry_status": get_expiry_status(stock_batch),
            "adjustment_form": adjustment_form,
            "damage_form": damage_form,
            "expired_form": expired_form,
        },
    )
