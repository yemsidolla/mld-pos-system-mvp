from datetime import timedelta
from decimal import Decimal

from django.contrib import messages
from django.db import models
from django.db.models import Count, DecimalField, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.shortcuts import render
from django.utils import timezone
from django.utils.dateparse import parse_date

from catalog.models import Product
from core.pagination import paginate
from core.permissions import reports_required
from inventory.models import InventoryMovement, StockBatch
from inventory.services import get_expiry_status
from pos.models import Sale


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


@reports_required
def reports_index_view(request):
    return render(request, "reports/index.html")


@reports_required
def daily_sales_report_view(request):
    requested_date = request.GET.get("date")
    report_date = parse_date(requested_date) if requested_date else timezone.localdate()
    if requested_date and report_date is None:
        report_date = timezone.localdate()
        messages.warning(request, "Invalid report date. Showing today's sales.")
    sales = Sale.objects.select_related("cashier").filter(created_at__date=report_date)
    completed_sales = sales.filter(status=Sale.Status.COMPLETED)
    totals = completed_sales.aggregate(
        sale_count=Count("id"),
        total_amount=Coalesce(
            Sum("final_amount"),
            Value(Decimal("0.00")),
            output_field=DecimalField(max_digits=12, decimal_places=2),
        ),
    )
    return render(
        request,
        "reports/daily_sales.html",
        {"report_date": report_date.isoformat(), "sales": sales, "totals": totals},
    )


@reports_required
def stock_summary_report_view(request):
    products = with_sellable_stock(Product.objects.all()).order_by("name")
    return render(request, "reports/stock_summary.html", {"products": products})


@reports_required
def low_stock_report_view(request):
    products = (
        with_sellable_stock(Product.objects.all())
        .filter(total_available__lte=models.F("min_stock"))
        .order_by("name")
    )
    return render(request, "reports/low_stock.html", {"products": products})


@reports_required
def expiry_report_view(request):
    today = timezone.localdate()
    warning_date = today + timedelta(days=60)
    batches = (
        StockBatch.objects.select_related("product", "supplier")
        .filter(product__is_active=True, status=StockBatch.Status.ACTIVE, quantity_available__gt=0, expiry_date__lte=warning_date)
        .order_by("expiry_date", "batch_no")
    )
    rows = [{"batch": batch, "expiry_status": get_expiry_status(batch, today=today)} for batch in batches]
    return render(request, "reports/expiry.html", {"rows": rows})


@reports_required
def stock_movement_report_view(request):
    movements = InventoryMovement.objects.select_related("product", "stock_batch", "created_by").order_by(
        "-created_at"
    )
    page_obj, querystring = paginate(request, movements, per_page=50)
    return render(
        request,
        "reports/stock_movements.html",
        {"movements": page_obj, "page_obj": page_obj, "querystring": querystring},
    )


@reports_required
def staff_sales_report_view(request):
    rows = (
        Sale.objects.filter(status=Sale.Status.COMPLETED)
        .values("cashier__username")
        .annotate(
            sale_count=Count("id"),
            total_sales=Coalesce(
                Sum("final_amount"),
                Value(Decimal("0.00")),
                output_field=DecimalField(max_digits=12, decimal_places=2),
            ),
        )
        .order_by("cashier__username")
    )
    return render(request, "reports/staff_sales.html", {"rows": rows})
