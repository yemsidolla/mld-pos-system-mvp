from datetime import timedelta
from decimal import Decimal

from django.db import models
from django.db.models import Count, DecimalField, Sum, Value
from django.db.models.functions import Coalesce
from django.shortcuts import render
from django.utils import timezone

from catalog.models import Product
from core.permissions import admin_required
from inventory.models import InventoryMovement, StockBatch
from inventory.services import get_expiry_status
from pos.models import Sale


@admin_required
def reports_index_view(request):
    return render(request, "reports/index.html")


@admin_required
def daily_sales_report_view(request):
    report_date = request.GET.get("date") or timezone.localdate().isoformat()
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
        {"report_date": report_date, "sales": sales, "totals": totals},
    )


@admin_required
def stock_summary_report_view(request):
    products = Product.objects.annotate(
        total_available=Coalesce(Sum("stock_batches__quantity_available"), 0)
    ).order_by("name")
    return render(request, "reports/stock_summary.html", {"products": products})


@admin_required
def low_stock_report_view(request):
    products = (
        Product.objects.annotate(total_available=Coalesce(Sum("stock_batches__quantity_available"), 0))
        .filter(total_available__lte=models.F("min_stock"))
        .order_by("name")
    )
    return render(request, "reports/low_stock.html", {"products": products})


@admin_required
def expiry_report_view(request):
    today = timezone.localdate()
    warning_date = today + timedelta(days=60)
    batches = (
        StockBatch.objects.select_related("product", "supplier")
        .filter(expiry_date__lte=warning_date)
        .order_by("expiry_date", "batch_no")
    )
    rows = [{"batch": batch, "expiry_status": get_expiry_status(batch, today=today)} for batch in batches]
    return render(request, "reports/expiry.html", {"rows": rows})


@admin_required
def stock_movement_report_view(request):
    movements = InventoryMovement.objects.select_related("product", "stock_batch", "created_by").order_by("-created_at")[:300]
    return render(request, "reports/stock_movements.html", {"movements": movements})


@admin_required
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
