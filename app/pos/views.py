from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from audit.models import AuditLog
from audit.services import create_audit_log
from inventory.models import StockBatch
from core.models import StoreSetting
from core.pagination import paginate
from core.permissions import admin_required, pos_required, sales_history_required

from .forms import CancelSaleForm, ConfirmSaleForm, PromotionForm, SaleFilterForm, ScanForm
from datetime import timedelta

from django.db.models import Sum
from django.utils import timezone

from .models import Promotion, Sale, SaleItem
from .pricing import choose_best_promotion, get_cost_snapshot, money
from .services import cancel_sale, confirm_sale, scan_code, validate_sellable_batch


MAX_HELD_SALES = 10


def _carts_state(request):
    """Multi-cart session state: {"carts": [{"id", "items"}], "active": id}.

    Migrates the legacy single-cart "pos_cart" key on first access so open
    carts survive the V8 upgrade.
    """
    state = request.session.get("pos_carts")
    if state is None:
        legacy = request.session.pop("pos_cart", None) or []
        state = {"carts": [{"id": 1, "items": legacy}], "active": 1}
        request.session["pos_carts"] = state
        request.session.modified = True
    return state


def _save_carts_state(request, state):
    # Drop empty parked carts so the tab row only shows real held sales.
    state["carts"] = [
        cart for cart in state["carts"] if cart["items"] or cart["id"] == state["active"]
    ]
    request.session["pos_carts"] = state
    request.session.modified = True


def _active_cart(state):
    for cart in state["carts"]:
        if cart["id"] == state["active"]:
            return cart
    state["active"] = state["carts"][0]["id"]
    return state["carts"][0]


QUICK_KEY_LIMIT = 12


def get_quick_keys():
    """Hand-picked quick-key products, else last-30-days top sellers."""
    picked = list(
        StoreSetting.load().quick_key_products.filter(is_active=True)[:QUICK_KEY_LIMIT]
    )
    if picked:
        return picked
    since = timezone.now() - timedelta(days=30)
    top = (
        SaleItem.objects.filter(
            sale__status=Sale.Status.COMPLETED,
            sale__created_at__gte=since,
            product__is_active=True,
        )
        .values("product")
        .annotate(total_quantity=Sum("quantity"))
        .order_by("-total_quantity")[:8]
    )
    from catalog.models import Product

    products = {p.pk: p for p in Product.objects.filter(pk__in=[row["product"] for row in top])}
    return [products[row["product"]] for row in top if row["product"] in products]


def get_promo_keys():
    """Active product-level promotions valid today, as POS tap keys."""
    today = timezone.localdate()
    promotions = (
        Promotion.objects.select_related("product")
        .filter(
            is_active=True,
            product__isnull=False,
            product__is_active=True,
            start_date__lte=today,
            end_date__gte=today,
        )
        .order_by("end_date")[:QUICK_KEY_LIMIT]
    )
    keys = []
    for promotion in promotions:
        if promotion.discount_type == Promotion.DiscountType.PERCENTAGE:
            tag = f"-{promotion.value.normalize():f}%"
        elif promotion.discount_type == Promotion.DiscountType.FIXED_AMOUNT:
            tag = f"-{promotion.value}"
        else:
            tag = f"= {promotion.value}"
        keys.append({"product": promotion.product, "promotion": promotion, "tag": tag})
    return keys


def get_cart(request):
    return _active_cart(_carts_state(request))["items"]


def save_cart(request, cart):
    state = _carts_state(request)
    _active_cart(state)["items"] = cart
    _save_carts_state(request, state)


def hold_current_sale(request):
    """Park the active cart and start a new empty one. Returns an error string."""
    state = _carts_state(request)
    if not _active_cart(state)["items"]:
        return "Cart is empty — nothing to hold."
    if len(state["carts"]) >= MAX_HELD_SALES:
        return f"Limit of {MAX_HELD_SALES} open sales reached. Complete or clear one first."
    new_id = max(cart["id"] for cart in state["carts"]) + 1
    state["carts"].append({"id": new_id, "items": []})
    state["active"] = new_id
    _save_carts_state(request, state)
    return ""


def resume_sale(request, cart_id):
    state = _carts_state(request)
    if not any(cart["id"] == cart_id for cart in state["carts"]):
        return "That held sale no longer exists."
    state["active"] = cart_id
    _save_carts_state(request, state)
    return ""


def carts_summary(request):
    state = _carts_state(request)
    return [
        {
            "id": cart["id"],
            "count": sum(item["quantity"] for item in cart["items"]),
            "active": cart["id"] == state["active"],
        }
        for cart in state["carts"]
    ]


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
        promotion_price = choose_best_promotion(stock_batch)
        original_subtotal = money(promotion_price.original_unit_price * item["quantity"])
        subtotal = money(promotion_price.final_unit_price * item["quantity"])
        total += subtotal
        cost_snapshot = get_cost_snapshot(stock_batch)
        below_cost = promotion_price.final_unit_price < cost_snapshot.cost_basis and not (
            promotion_price.promotion and promotion_price.promotion.allow_below_cost
        )
        rows.append(
            {
                "stock_batch": stock_batch,
                "below_cost": below_cost,
                "quantity": item["quantity"],
                "original_unit_price": promotion_price.original_unit_price,
                "final_unit_price": promotion_price.final_unit_price,
                "original_subtotal": original_subtotal,
                "subtotal": subtotal,
                "promotion": promotion_price.promotion,
                "promotion_name": promotion_price.promotion_name,
                "discount_amount": money(promotion_price.discount_per_unit * item["quantity"]),
            }
        )
    return rows, total


def _promotion_snapshot(promotion):
    if promotion is None:
        return None
    return {
        "name": promotion.name,
        "discount_type": promotion.discount_type,
        "value": str(promotion.value),
        "start_date": promotion.start_date.isoformat(),
        "end_date": promotion.end_date.isoformat(),
        "is_active": promotion.is_active,
        "product": promotion.product.product_code if promotion.product_id else None,
        "category": promotion.category.name if promotion.category_id else None,
        "allow_below_cost": promotion.allow_below_cost,
    }


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
                    if len(available_batches) == 1:
                        # One sellable batch: skip the picker and add it directly.
                        only_batch = available_batches[0]
                        add_batch_to_cart(request, only_batch, 1)
                        messages.success(request, f"Added {only_batch.batch_no} to cart.")
                        return redirect("pos-sale")
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
            elif action == "hold":
                error = hold_current_sale(request)
                if error:
                    messages.error(request, error)
                else:
                    messages.success(request, "Sale held. Started a new sale.")
                return redirect("pos-sale")
            elif action == "resume":
                error = resume_sale(request, int(request.POST.get("cart_id", "0")))
                if error:
                    messages.error(request, error)
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
                        override_reason=confirm_form.cleaned_data["override_reason"],
                        request=request,
                    )
                    save_cart(request, [])
                    messages.success(request, f"Sale {sale.sale_no} completed.")
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
            "carts_summary": carts_summary(request),
            "quick_keys": get_quick_keys(),
            "promo_keys": get_promo_keys(),
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
    return render(
        request,
        "pos/receipt.html",
        {
            "sale": sale,
            "store": StoreSetting.load(),
            "auto_print": request.GET.get("print") == "1",
        },
    )


@admin_required
def sale_reprint_view(request, sale_id):
    sale = get_object_or_404(Sale, pk=sale_id)
    if request.method != "POST":
        return redirect("sale-detail", sale_id=sale.id)
    create_audit_log(
        action=AuditLog.Action.RECEIPT_PRINT,
        module="pos",
        request=request,
        object_type="Sale",
        object_id=sale.pk,
        object_display=sale.sale_no,
        new_value={"reprint": True},
    )
    return redirect(f"{reverse('sale-receipt', args=[sale.id])}?print=1")


@sales_history_required
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
    page_obj, querystring = paginate(request, sales)
    return render(
        request,
        "pos/sales_history.html",
        {"form": form, "sales": page_obj, "page_obj": page_obj, "querystring": querystring},
    )


@sales_history_required
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


@admin_required
def promotion_list_view(request):
    query = request.GET.get("q", "").strip()
    promotions = Promotion.objects.select_related("product", "category", "created_by").order_by("-is_active", "name")
    if query:
        promotions = promotions.filter(
            Q(name__icontains=query)
            | Q(product__name__icontains=query)
            | Q(product__product_code__icontains=query)
            | Q(category__name__icontains=query)
        )
    return render(
        request,
        "pos/promotion_list.html",
        {"promotions": promotions, "query": query, "promotion_count": promotions.count()},
    )


def _promotion_form_view(request, *, instance, mode):
    old_value = _promotion_snapshot(instance)
    form = PromotionForm(request.POST or None, instance=instance, created_by=request.user)
    if request.method == "POST" and form.is_valid():
        promotion = form.save()
        new_value = _promotion_snapshot(promotion)
        if mode == "create":
            action = AuditLog.Action.PROMOTION_CREATE
        elif old_value and old_value["is_active"] and not promotion.is_active:
            action = AuditLog.Action.PROMOTION_DEACTIVATE
        else:
            action = AuditLog.Action.PROMOTION_UPDATE
        create_audit_log(
            action=action,
            module="pos",
            user=request.user,
            request=request,
            object_type="Promotion",
            object_id=promotion.pk,
            object_display=promotion.name,
            old_value=old_value,
            new_value=new_value,
        )
        messages.success(request, f"Promotion {promotion.name} was saved.")
        return redirect("promotion-list")
    return render(request, "pos/promotion_form.html", {"form": form, "mode": mode, "promotion": instance})


@admin_required
def promotion_create_view(request):
    return _promotion_form_view(request, instance=None, mode="create")


@admin_required
def promotion_edit_view(request, promotion_id):
    promotion = get_object_or_404(Promotion, pk=promotion_id)
    return _promotion_form_view(request, instance=promotion, mode="edit")
