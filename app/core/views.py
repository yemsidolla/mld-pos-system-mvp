import logging

from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import ValidationError
from django.db import connections
from django.db.models import F, Sum
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_GET

from batch_upload.models import BatchUploadJob
from catalog.models import Product
from inventory.models import StockBatch
from pos.models import Sale
from pos.services import parse_custom_code

from .permissions import can_access_pos, is_admin_user


logger = logging.getLogger(__name__)


def health_check(request):
    status_code = 200
    payload = {
        "service": "Melodu POS & Inventory Control System",
        "status": "ok",
        "database": "ok",
    }

    try:
        with connections["default"].cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception as exc:
        logger.exception("Health check database probe failed.")
        payload["status"] = "degraded"
        payload["database"] = "error"
        payload["error"] = exc.__class__.__name__
        status_code = 503

    return JsonResponse(payload, status=status_code)


def _product_payload(product):
    return {
        "id": product.id,
        "product_code": product.product_code,
        "name": product.name,
        "original_barcode": product.original_barcode,
        "is_active": product.is_active,
        "default_selling_price": str(product.default_selling_price),
    }


def _batch_payload(stock_batch):
    return {
        "id": stock_batch.id,
        "batch_no": stock_batch.batch_no,
        "custom_code": stock_batch.custom_code,
        "status": stock_batch.status,
        "expiry_date": stock_batch.expiry_date.isoformat(),
        "quantity_available": stock_batch.quantity_available,
        "selling_price": str(stock_batch.selling_price),
        "supplier": stock_batch.supplier.name,
    }


def _resolve_warnings(product=None, stock_batch=None):
    warnings = []
    if product is not None and not product.is_active:
        warnings.append("Product is inactive.")
    if stock_batch is not None:
        if stock_batch.status != StockBatch.Status.ACTIVE:
            warnings.append(f"Batch status is {stock_batch.status}.")
        if stock_batch.quantity_available <= 0:
            warnings.append("Batch has no available quantity.")
        if stock_batch.expiry_date < timezone.localdate():
            warnings.append("Batch is expired.")
    return warnings


@user_passes_test(can_access_pos)
def dashboard_home_view(request):
    today = timezone.localdate()
    context = {
        "today": today,
        "recent_sales": [],
        "recent_uploads": [],
        "stats": {},
    }

    if is_admin_user(request.user):
        active_batches = StockBatch.objects.filter(status=StockBatch.Status.ACTIVE)
        context["stats"] = {
            "products": Product.objects.filter(is_active=True).count(),
            "active_batches": active_batches.count(),
            "low_stock_products": Product.objects.filter(stock_batches__isnull=False)
            .annotate(total_available=Sum("stock_batches__quantity_available"))
            .filter(total_available__lte=F("min_stock"))
            .distinct()
            .count(),
            "today_sales": Sale.objects.filter(created_at__date=today).count(),
        }
        context["recent_sales"] = Sale.objects.select_related("cashier").order_by("-created_at")[:5]
        context["recent_uploads"] = BatchUploadJob.objects.select_related("uploaded_by").order_by("-created_at")[:5]
    else:
        context["stats"] = {
            "today_sales": Sale.objects.filter(cashier=request.user, created_at__date=today).count(),
            "cart_ready": 1,
        }
        context["recent_sales"] = Sale.objects.filter(cashier=request.user).order_by("-created_at")[:5]

    from django.shortcuts import render

    return render(request, "dashboard/home.html", context)


@require_GET
@user_passes_test(can_access_pos)
def scan_resolve_view(request):
    value = request.GET.get("value", "").strip()
    context = request.GET.get("context", "").strip() or "general"
    if not value:
        return JsonResponse({"status": "error", "error": "Scan value is required."}, status=400)

    if "-" in value:
        try:
            parsed = parse_custom_code(value)
        except ValidationError as exc:
            return JsonResponse({"status": "error", "error": "; ".join(exc.messages)}, status=400)

        stock_batch = (
            StockBatch.objects.select_related("product", "supplier")
            .filter(batch_no=parsed.batch_no)
            .first()
        )
        if stock_batch is None:
            return JsonResponse({"status": "error", "error": "Batch number does not exist."}, status=404)
        if stock_batch.product.original_barcode != parsed.original_barcode:
            return JsonResponse({"status": "error", "error": "Product and batch do not match."}, status=400)
        if stock_batch.expiry_date.strftime("%y%m%d") != parsed.expiry_yymmdd:
            return JsonResponse({"status": "error", "error": "Expiry date does not match stock batch."}, status=400)
        return JsonResponse(
            {
                "status": "ok",
                "context": context,
                "match_type": "custom_code",
                "product": _product_payload(stock_batch.product),
                "stock_batch": _batch_payload(stock_batch),
                "warnings": _resolve_warnings(stock_batch.product, stock_batch),
            }
        )

    stock_batch = (
        StockBatch.objects.select_related("product", "supplier")
        .filter(batch_no=value)
        .first()
    )
    if stock_batch is not None:
        return JsonResponse(
            {
                "status": "ok",
                "context": context,
                "match_type": "batch_no",
                "product": _product_payload(stock_batch.product),
                "stock_batch": _batch_payload(stock_batch),
                "warnings": _resolve_warnings(stock_batch.product, stock_batch),
            }
        )

    product = Product.objects.filter(product_code=value).first()
    match_type = "product_code"
    if product is None:
        product = Product.objects.filter(original_barcode=value).first()
        match_type = "original_barcode"
    if product is None:
        return JsonResponse({"status": "error", "error": "No product or stock batch found."}, status=404)

    batches = [
        _batch_payload(batch)
        for batch in StockBatch.objects.select_related("supplier")
        .filter(product=product)
        .order_by("expiry_date", "batch_no")[:10]
    ]
    return JsonResponse(
        {
            "status": "ok",
            "context": context,
            "match_type": match_type,
            "product": _product_payload(product),
            "stock_batches": batches,
            "warnings": _resolve_warnings(product),
        }
    )
