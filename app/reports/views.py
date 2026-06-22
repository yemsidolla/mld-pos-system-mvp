from datetime import timedelta
from decimal import Decimal

from django.contrib import messages
from django.db import models
from django.db.models import Count, DecimalField, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.shortcuts import render
from django.utils import timezone
from django.utils.dateparse import parse_date

from audit.models import AuditLog
from catalog.models import Product
from core.pagination import paginate
from core.permissions import can_view_costs, reports_required
from inventory.models import InventoryMovement, StockBatch
from inventory.services import get_expiry_status
from pos.models import Sale, SaleItem


def sellable_stock_filter(today=None):
    today = today or timezone.localdate()
    return Q(stock_batches__status=StockBatch.Status.ACTIVE, stock_batches__expiry_date__gte=today)


def with_sellable_stock(queryset, today=None):
    return queryset.filter(is_active=True).annotate(
        total_available=Coalesce(
            Sum("stock_batches__quantity_available", filter=sellable_stock_filter(today)),
            0,
        )
    )


def apply_stock_action_context(products):
    for product in products:
        total_available = product.total_available or 0
        product.reorder_gap = max(product.min_stock - total_available, 0)
        if total_available <= 0:
            product.stock_action_label = "Out of stock"
            product.stock_action_class = "badge-danger"
        elif total_available <= product.min_stock:
            product.stock_action_label = "Low stock"
            product.stock_action_class = "badge-warning"
        else:
            product.stock_action_label = "OK"
            product.stock_action_class = "badge-success"
    return products


def expiry_action_for_status(expiry_status):
    if expiry_status == "Expired":
        return "Remove from sale"
    if expiry_status == "Critical":
        return "Review today"
    if expiry_status == "Warning":
        return "Plan rotation"
    return "Monitor"


@reports_required
def reports_index_view(request):
    return render(request, "reports/index.html")


@reports_required
def daily_closing_checklist_view(request):
    checklist_sections = [
        {
            "title": "Sales and cash",
            "items": [
                "Review Daily Sales for completed revenue, cancelled exceptions, discounts, and payment breakdown.",
                "Compare cash drawer or payment terminal totals with the payment breakdown.",
                "Open suspicious sales from Daily Sales or Sales History before closing.",
            ],
        },
        {
            "title": "Staff accountability",
            "items": [
                "Review Staff Sales for cashier totals, cancellations, receipt reprints, and overrides.",
                "Ask for explanations on unusual exception counts before accepting the day.",
            ],
        },
        {
            "title": "Stock risk",
            "items": [
                "Review Low Stock and Expiry reports for items that need receiving, rotation, or removal from sale.",
                "Confirm urgent stock actions are assigned before the next selling day.",
            ],
        },
        {
            "title": "Promotion risk",
            "items": [
                "Review Promotion & Below-cost Report for heavy discounts, below-cost lines, and overrides.",
                "Disable or edit unsafe promotions from the Promotions page if needed.",
            ],
        },
        {
            "title": "System and backup posture",
            "items": [
                "Review System Health and Live Logs for errors or capacity warnings.",
                "Confirm the latest backup according to the deployment/backup runbook.",
            ],
        },
    ]
    return render(
        request,
        "reports/daily_closing_checklist.html",
        {"checklist_sections": checklist_sections},
    )


@reports_required
def daily_sales_report_view(request):
    requested_date = request.GET.get("date")
    report_date = parse_date(requested_date) if requested_date else timezone.localdate()
    if requested_date and report_date is None:
        report_date = timezone.localdate()
        messages.warning(request, "Invalid report date. Showing today's sales.")
    sales = Sale.objects.select_related("cashier").filter(created_at__date=report_date)
    completed_sales = sales.filter(status=Sale.Status.COMPLETED)
    cancelled_sales = sales.filter(status=Sale.Status.CANCELLED)
    totals = completed_sales.aggregate(
        sale_count=Count("id"),
        gross_amount=Coalesce(
            Sum("total_amount"),
            Value(Decimal("0.00")),
            output_field=DecimalField(max_digits=12, decimal_places=2),
        ),
        discount_amount=Coalesce(
            Sum("discount_amount"),
            Value(Decimal("0.00")),
            output_field=DecimalField(max_digits=12, decimal_places=2),
        ),
        total_amount=Coalesce(
            Sum("final_amount"),
            Value(Decimal("0.00")),
            output_field=DecimalField(max_digits=12, decimal_places=2),
        ),
    )
    totals["cancelled_count"] = cancelled_sales.count()
    totals["all_sale_count"] = sales.count()
    totals["average_sale"] = (
        totals["total_amount"] / totals["sale_count"] if totals["sale_count"] else Decimal("0.00")
    )

    payment_rows = []
    completed_by_payment = {
        row["payment_method"]: row
        for row in completed_sales.values("payment_method").annotate(
            sale_count=Count("id"),
            total_amount=Coalesce(
                Sum("final_amount"),
                Value(Decimal("0.00")),
                output_field=DecimalField(max_digits=12, decimal_places=2),
            ),
        )
    }
    for value, label in Sale.PaymentMethod.choices:
        row = completed_by_payment.get(value, {})
        payment_rows.append(
            {
                "value": value,
                "label": label,
                "sale_count": row.get("sale_count", 0),
                "total_amount": row.get("total_amount", Decimal("0.00")),
            }
        )

    user_can_view_costs = can_view_costs(request.user)
    cost_summary = {}
    if user_can_view_costs:
        cost_expr = models.ExpressionWrapper(
            models.F("cost_basis_at_sale") * models.F("quantity"),
            output_field=DecimalField(max_digits=12, decimal_places=2),
        )
        cost_total = (
            SaleItem.objects.filter(sale__created_at__date=report_date, sale__status=Sale.Status.COMPLETED)
            .aggregate(
                total_cost=Coalesce(
                    Sum(cost_expr),
                    Value(Decimal("0.00")),
                    output_field=DecimalField(max_digits=12, decimal_places=2),
                )
            )["total_cost"]
            or Decimal("0.00")
        )
        cost_summary = {
            "total_cost": cost_total,
            "gross_margin": totals["total_amount"] - cost_total,
        }
    return render(
        request,
        "reports/daily_sales.html",
        {
            "report_date": report_date.isoformat(),
            "sales": sales,
            "totals": totals,
            "payment_rows": payment_rows,
            "cost_summary": cost_summary,
            "user_can_view_costs": user_can_view_costs,
        },
    )


@reports_required
def stock_summary_report_view(request):
    products = apply_stock_action_context(list(with_sellable_stock(Product.objects.all()).order_by("name")))
    summary = {
        "product_count": len(products),
        "total_available": sum(product.total_available or 0 for product in products),
        "low_stock_count": sum(1 for product in products if (product.total_available or 0) <= product.min_stock),
        "out_of_stock_count": sum(1 for product in products if (product.total_available or 0) <= 0),
        "healthy_count": sum(1 for product in products if (product.total_available or 0) > product.min_stock),
        "reorder_units": sum(product.reorder_gap for product in products),
    }
    return render(request, "reports/stock_summary.html", {"products": products, "summary": summary})


@reports_required
def low_stock_report_view(request):
    products = apply_stock_action_context(list(
        with_sellable_stock(Product.objects.all())
        .filter(total_available__lte=models.F("min_stock"))
        .order_by("name")
    ))
    products = sorted(products, key=lambda product: (-product.reorder_gap, product.name))
    summary = {
        "product_count": len(products),
        "total_available": sum(product.total_available or 0 for product in products),
        "out_of_stock_count": sum(1 for product in products if (product.total_available or 0) <= 0),
        "reorder_units": sum(product.reorder_gap for product in products),
    }
    return render(request, "reports/low_stock.html", {"products": products, "summary": summary})


@reports_required
def expiry_report_view(request):
    today = timezone.localdate()
    warning_date = today + timedelta(days=60)
    batches = (
        StockBatch.objects.select_related("product", "supplier")
        .filter(product__is_active=True, status=StockBatch.Status.ACTIVE, quantity_available__gt=0, expiry_date__lte=warning_date)
        .order_by("expiry_date", "batch_no")
    )
    rows = []
    for batch in batches:
        expiry_status = get_expiry_status(batch, today=today)
        rows.append(
            {
                "batch": batch,
                "expiry_status": expiry_status,
                "days_until_expiry": (batch.expiry_date - today).days,
                "action_label": expiry_action_for_status(expiry_status),
            }
        )
    summary = {
        "batch_count": len(rows),
        "expired_count": sum(1 for row in rows if row["expiry_status"] == "Expired"),
        "critical_count": sum(1 for row in rows if row["expiry_status"] == "Critical"),
        "warning_count": sum(1 for row in rows if row["expiry_status"] == "Warning"),
        "review_now_count": sum(1 for row in rows if row["expiry_status"] in {"Expired", "Critical"}),
    }
    return render(request, "reports/expiry.html", {"rows": rows, "summary": summary})


@reports_required
def stock_movement_report_view(request):
    query = request.GET.get("q", "").strip()
    movement_type = request.GET.get("movement_type", "").strip()
    movements = InventoryMovement.objects.select_related("product", "stock_batch", "created_by").order_by(
        "-created_at"
    )
    movement_type_values = {choice[0] for choice in InventoryMovement.MovementType.choices}
    if movement_type in movement_type_values:
        movements = movements.filter(movement_type=movement_type)
    if query:
        movements = movements.filter(
            Q(product__name__icontains=query)
            | Q(product__product_code__icontains=query)
            | Q(stock_batch__batch_no__icontains=query)
            | Q(stock_batch__custom_code__icontains=query)
            | Q(reference_type__icontains=query)
            | Q(reference_id__icontains=query)
            | Q(note__icontains=query)
            | Q(created_by__username__icontains=query)
        )
    movement_count = movements.count()
    page_obj, querystring = paginate(request, movements, per_page=50)
    return render(
        request,
        "reports/stock_movements.html",
        {
            "movements": page_obj,
            "page_obj": page_obj,
            "querystring": querystring,
            "movement_count": movement_count,
            "query": query,
            "movement_type": movement_type,
            "movement_type_choices": InventoryMovement.MovementType.choices,
        },
    )


@reports_required
def staff_sales_report_view(request):
    base_rows = list(
        Sale.objects.values("cashier_id", "cashier__username")
        .annotate(
            sale_count=Count("id", filter=Q(status=Sale.Status.COMPLETED)),
            cancelled_count=Count("id", filter=Q(status=Sale.Status.CANCELLED)),
            total_sales=Coalesce(
                Sum("final_amount", filter=Q(status=Sale.Status.COMPLETED)),
                Value(Decimal("0.00")),
                output_field=DecimalField(max_digits=12, decimal_places=2),
            ),
            discount_total=Coalesce(
                Sum("discount_amount", filter=Q(status=Sale.Status.COMPLETED)),
                Value(Decimal("0.00")),
                output_field=DecimalField(max_digits=12, decimal_places=2),
            ),
        )
        .order_by("cashier__username")
    )

    sale_id_to_cashier_id = {
        str(sale.id): sale.cashier_id for sale in Sale.objects.only("id", "cashier_id")
    }
    reprint_counts = {}
    for object_id in AuditLog.objects.filter(action=AuditLog.Action.RECEIPT_PRINT, object_type="Sale").values_list(
        "object_id", flat=True
    ):
        cashier_id = sale_id_to_cashier_id.get(str(object_id))
        if cashier_id:
            reprint_counts[cashier_id] = reprint_counts.get(cashier_id, 0) + 1

    override_rows = (
        SaleItem.objects.filter(sale__status=Sale.Status.COMPLETED, override_by__isnull=False)
        .values("sale__cashier_id")
        .annotate(override_count=Count("id"))
    )
    override_counts = {row["sale__cashier_id"]: row["override_count"] for row in override_rows}

    user_can_view_costs = can_view_costs(request.user)
    cost_by_cashier = {}
    if user_can_view_costs:
        cost_expr = models.ExpressionWrapper(
            models.F("cost_basis_at_sale") * models.F("quantity"),
            output_field=DecimalField(max_digits=12, decimal_places=2),
        )
        cost_rows = (
            SaleItem.objects.filter(sale__status=Sale.Status.COMPLETED)
            .values("sale__cashier_id")
            .annotate(
                total_cost=Coalesce(
                    Sum(cost_expr),
                    Value(Decimal("0.00")),
                    output_field=DecimalField(max_digits=12, decimal_places=2),
                )
            )
        )
        cost_by_cashier = {row["sale__cashier_id"]: row["total_cost"] for row in cost_rows}

    rows = []
    for row in base_rows:
        cashier_id = row["cashier_id"]
        row["reprint_count"] = reprint_counts.get(cashier_id, 0)
        row["override_count"] = override_counts.get(cashier_id, 0)
        row["average_sale"] = row["total_sales"] / row["sale_count"] if row["sale_count"] else Decimal("0.00")
        if user_can_view_costs:
            row["total_cost"] = cost_by_cashier.get(cashier_id, Decimal("0.00"))
            row["gross_margin"] = row["total_sales"] - row["total_cost"]
        rows.append(row)

    summary = {
        "staff_count": len(rows),
        "sale_count": sum(row["sale_count"] or 0 for row in rows),
        "cancelled_count": sum(row["cancelled_count"] or 0 for row in rows),
        "reprint_count": sum(row["reprint_count"] or 0 for row in rows),
        "override_count": sum(row["override_count"] or 0 for row in rows),
        "discount_total": sum(row["discount_total"] or Decimal("0.00") for row in rows),
        "total_sales": sum(row["total_sales"] or Decimal("0.00") for row in rows),
    }
    if user_can_view_costs:
        summary["total_cost"] = sum(row["total_cost"] or Decimal("0.00") for row in rows)
        summary["gross_margin"] = sum(row["gross_margin"] or Decimal("0.00") for row in rows)
    return render(
        request,
        "reports/staff_sales.html",
        {"rows": rows, "summary": summary, "user_can_view_costs": user_can_view_costs},
    )


@reports_required
def promotion_report_view(request):
    user_can_view_costs = can_view_costs(request.user)
    promoted_items = (
        SaleItem.objects.select_related("sale", "product", "stock_batch")
        .filter(sale__status=Sale.Status.COMPLETED)
        .exclude(promotion_name_at_sale="")
        .order_by("promotion_name_at_sale", "-sale__created_at")
    )

    promotion_map = {}
    below_cost_items = []
    for item in promoted_items:
        name = item.promotion_name_at_sale
        row = promotion_map.setdefault(
            name,
            {
                "promotion_name": name,
                "line_count": 0,
                "quantity": 0,
                "gross_amount": Decimal("0.00"),
                "discount_amount": Decimal("0.00"),
                "final_amount": Decimal("0.00"),
                "below_cost_count": 0,
                "override_count": 0,
                "total_cost": Decimal("0.00"),
                "gross_margin": Decimal("0.00"),
            },
        )
        quantity = item.quantity or 0
        gross_amount = (item.original_unit_price or Decimal("0.00")) * quantity
        discount_amount = (item.discount_amount or Decimal("0.00")) * quantity
        final_amount = item.subtotal or (item.final_unit_price or Decimal("0.00")) * quantity
        cost_amount = (item.cost_basis_at_sale or Decimal("0.00")) * quantity
        is_below_cost = item.final_unit_price < item.cost_basis_at_sale

        row["line_count"] += 1
        row["quantity"] += quantity
        row["gross_amount"] += gross_amount
        row["discount_amount"] += discount_amount
        row["final_amount"] += final_amount
        row["total_cost"] += cost_amount
        row["gross_margin"] += final_amount - cost_amount
        if is_below_cost:
            row["below_cost_count"] += 1
            below_cost_items.append(item)
        if item.override_by_id:
            row["override_count"] += 1

    rows = list(promotion_map.values())
    summary = {
        "promotion_count": len(rows),
        "line_count": sum(row["line_count"] for row in rows),
        "quantity": sum(row["quantity"] for row in rows),
        "discount_amount": sum(row["discount_amount"] for row in rows),
        "final_amount": sum(row["final_amount"] for row in rows),
        "below_cost_count": sum(row["below_cost_count"] for row in rows),
        "override_count": sum(row["override_count"] for row in rows),
    }
    if user_can_view_costs:
        summary["total_cost"] = sum(row["total_cost"] for row in rows)
        summary["gross_margin"] = sum(row["gross_margin"] for row in rows)

    return render(
        request,
        "reports/promotion_report.html",
        {
            "rows": rows,
            "summary": summary,
            "below_cost_items": below_cost_items[:25],
            "user_can_view_costs": user_can_view_costs,
        },
    )
