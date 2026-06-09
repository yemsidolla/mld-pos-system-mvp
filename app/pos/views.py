from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from inventory.models import StockBatch
from core.permissions import admin_required, pos_required

from .forms import CancelSaleForm, ConfirmSaleForm, SaleFilterForm, ScanForm
from .models import Sale
from .services import cancel_sale, confirm_sale, scan_code, validate_sellable_batch


def get_cart(request):
    return request.session.setdefault("pos_cart", [])


def save_cart(request, cart):
    request.session["pos_cart"] = cart
    request.session.modified = True


def add_batch_to_cart(request, stock_batch, quantity=1):
    if quantity <= 0:
        raise ValidationError("Sale quantity must be greater than zero.")
    cart = get_cart(request)
    for item in cart:
        if item["stock_batch_id"] == stock_batch.id:
            new_quantity = item["quantity"] + quantity
            validate_sellable_batch(stock_batch, quantity=new_quantity)
            item["quantity"] = new_quantity
            save_cart(request, cart)
            return
    validate_sellable_batch(stock_batch, quantity=quantity)
    cart.append({"stock_batch_id": stock_batch.id, "quantity": quantity})
    save_cart(request, cart)


def update_cart_item(request, stock_batch, quantity):
    if quantity <= 0:
        raise ValidationError("Sale quantity must be greater than zero.")
    validate_sellable_batch(stock_batch, quantity=quantity)
    cart = get_cart(request)
    for item in cart:
        if item["stock_batch_id"] == stock_batch.id:
            item["quantity"] = quantity
            save_cart(request, cart)
            return
    raise ValidationError("Cart item does not exist.")


def remove_cart_item(request, stock_batch_id):
    cart = [item for item in get_cart(request) if item["stock_batch_id"] != stock_batch_id]
    save_cart(request, cart)


def get_cart_rows(request):
    cart = get_cart(request)
    batch_ids = [item["stock_batch_id"] for item in cart]
    batches = {
        batch.id: batch
        for batch in StockBatch.objects.select_related("product").filter(id__in=batch_ids)
    }
    rows = []
    total = 0
    for item in cart:
        stock_batch = batches.get(item["stock_batch_id"])
        if stock_batch is None:
            continue
        subtotal = stock_batch.selling_price * item["quantity"]
        total += subtotal
        rows.append({"stock_batch": stock_batch, "quantity": item["quantity"], "subtotal": subtotal})
    return rows, total


@pos_required
def pos_sale_view(request):
    scan_form = ScanForm()
    confirm_form = ConfirmSaleForm()
    scanned_product = None
    available_batches = []

    if request.method == "POST":
        action = request.POST.get("action")
        if not action and request.POST.get("scan_value"):
            action = "scan"
        try:
            if action == "scan":
                scan_form = ScanForm(request.POST)
                if scan_form.is_valid():
                    result = scan_code(scan_form.cleaned_data["scan_value"])
                    if result["scan_type"] == "CUSTOM_CODE":
                        add_batch_to_cart(request, result["stock_batch"], 1)
                        messages.success(request, f"Added {result['stock_batch'].batch_no} to cart.")
                        return redirect("pos-sale")
                    scanned_product = result["product"]
                    available_batches = result["available_batches"]
            elif action == "add_batch":
                stock_batch = get_object_or_404(StockBatch.objects.select_related("product"), pk=request.POST.get("stock_batch_id"))
                quantity = int(request.POST.get("quantity", "1"))
                add_batch_to_cart(request, stock_batch, quantity)
                messages.success(request, f"Added {stock_batch.batch_no} to cart.")
                return redirect("pos-sale")
            elif action == "update_item":
                stock_batch = get_object_or_404(StockBatch.objects.select_related("product"), pk=request.POST.get("stock_batch_id"))
                quantity = int(request.POST.get("quantity", "1"))
                update_cart_item(request, stock_batch, quantity)
                messages.success(request, f"Updated {stock_batch.batch_no}.")
                return redirect("pos-sale")
            elif action == "remove_item":
                stock_batch_id = int(request.POST.get("stock_batch_id"))
                remove_cart_item(request, stock_batch_id)
                messages.success(request, "Item removed from cart.")
                return redirect("pos-sale")
            elif action == "clear":
                save_cart(request, [])
                return redirect("pos-sale")
            elif action == "confirm":
                confirm_form = ConfirmSaleForm(request.POST)
                if confirm_form.is_valid():
                    cart_rows, _total = get_cart_rows(request)
                    sale = confirm_sale(
                        cart_items=[
                            {"stock_batch": row["stock_batch"], "quantity": row["quantity"]}
                            for row in cart_rows
                        ],
                        cashier=request.user,
                        payment_method=confirm_form.cleaned_data["payment_method"],
                        discount_amount=confirm_form.cleaned_data["discount_amount"],
                        request=request,
                    )
                    save_cart(request, [])
                    return redirect(reverse("sale-receipt", kwargs={"sale_id": sale.id}))
        except ValidationError as exc:
            messages.error(request, "; ".join(exc.messages))
        except ValueError:
            messages.error(request, "Invalid quantity.")

    cart_rows, cart_total = get_cart_rows(request)
    return render(
        request,
        "pos/pos_sale.html",
        {
            "scan_form": scan_form,
            "confirm_form": confirm_form,
            "scanned_product": scanned_product,
            "available_batches": available_batches,
            "cart_rows": cart_rows,
            "cart_total": cart_total,
        },
    )


@pos_required
def sale_receipt_view(request, sale_id):
    sale = get_object_or_404(Sale.objects.prefetch_related("items__product", "items__stock_batch"), pk=sale_id)
    return render(request, "pos/receipt.html", {"sale": sale})


@admin_required
def sales_history_view(request):
    form = SaleFilterForm(request.GET or None)
    sales = Sale.objects.select_related("cashier").all()
    if form.is_valid():
        if form.cleaned_data["date_from"]:
            sales = sales.filter(created_at__date__gte=form.cleaned_data["date_from"])
        if form.cleaned_data["date_to"]:
            sales = sales.filter(created_at__date__lte=form.cleaned_data["date_to"])
        if form.cleaned_data["cashier"]:
            sales = sales.filter(cashier=form.cleaned_data["cashier"])
        if form.cleaned_data["payment_method"]:
            sales = sales.filter(payment_method=form.cleaned_data["payment_method"])
    return render(request, "pos/sales_history.html", {"form": form, "sales": sales})


@admin_required
def sale_detail_view(request, sale_id):
    sale = get_object_or_404(
        Sale.objects.select_related("cashier").prefetch_related("items__product", "items__stock_batch"),
        pk=sale_id,
    )
    cancel_form = CancelSaleForm()
    return render(request, "pos/sale_detail.html", {"sale": sale, "cancel_form": cancel_form})


@admin_required
def sale_cancel_view(request, sale_id):
    sale = get_object_or_404(Sale, pk=sale_id)
    if request.method != "POST":
        return redirect("sale-detail", sale_id=sale.id)

    form = CancelSaleForm(request.POST)
    if form.is_valid():
        try:
            cancel_sale(
                sale=sale,
                cancelled_by=request.user,
                reason=form.cleaned_data["reason"],
                request=request,
            )
        except ValidationError as exc:
            messages.error(request, "; ".join(exc.messages))
        else:
            messages.success(request, f"Sale {sale.sale_no} was cancelled.")
            return redirect("sale-detail", sale_id=sale.id)
    else:
        messages.error(request, "Cancellation reason is required.")
    return redirect("sale-detail", sale_id=sale.id)
