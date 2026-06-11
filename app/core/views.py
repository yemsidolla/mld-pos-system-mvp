import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from django.db import connections
from django.db.migrations.executor import MigrationExecutor
from django.db.models import F, Sum
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from batch_upload.models import BatchUploadJob
from catalog.models import Product
from inventory.models import StockBatch
from pos.models import Sale
from pos.services import parse_custom_code

from audit.models import AuditLog
from audit.services import create_audit_log

from .forms import StoreSettingForm
from .models import StoreSetting
from .permissions import (
    can_access_dashboard,
    can_access_pos,
    can_manage_catalog,
    can_manage_inventory,
    can_view_reports,
    can_view_sales_history,
    dashboard_required,
    is_admin_user,
    is_cashier_user,
    settings_required,
)


logger = logging.getLogger(__name__)


def _safe_next_url(request):
    next_url = request.POST.get("next") or request.GET.get("next") or ""
    if next_url and url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return next_url
    return ""


@never_cache
@require_http_methods(["GET", "POST"])
def dashboard_login_view(request):
    if request.user.is_authenticated:
        return redirect(settings.LOGIN_REDIRECT_URL)

    safe_next = _safe_next_url(request)
    form = AuthenticationForm(request, data=request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            auth_login(request, form.get_user())
            return redirect(safe_next or settings.LOGIN_REDIRECT_URL)
        messages.error(request, "Check your username and password, then try again.")

    return render(request, "dashboard/login.html", {"form": form, "next": safe_next})


@never_cache
@require_POST
def dashboard_logout_view(request):
    if request.user.is_authenticated:
        auth_logout(request)
    messages.success(request, "You have logged out successfully.")
    return redirect(settings.LOGOUT_REDIRECT_URL)


def _store_setting_snapshot(setting):
    return {
        "store_name": setting.store_name,
        "address": setting.address,
        "phone": setting.phone,
        "receipt_header": setting.receipt_header,
        "receipt_footer": setting.receipt_footer,
        "receipt_paper_width_mm": setting.receipt_paper_width_mm,
        "receipt_font_size_px": setting.receipt_font_size_px,
        "show_logo_on_receipt": setting.show_logo_on_receipt,
        "currency_symbol": setting.currency_symbol,
    }


@settings_required
def store_settings_view(request):
    setting = StoreSetting.load()
    old_value = _store_setting_snapshot(setting)
    form = StoreSettingForm(request.POST or None, request.FILES or None, instance=setting)

    if request.method == "POST" and form.is_valid():
        setting = form.save()
        create_audit_log(
            action=AuditLog.Action.SETTING_CHANGE,
            module="core",
            request=request,
            object_type="StoreSetting",
            object_id=setting.pk,
            object_display=setting.store_name,
            old_value=old_value,
            new_value=_store_setting_snapshot(setting),
        )
        messages.success(request, "Store settings were updated.")
        return redirect("store-settings")

    return render(request, "core/store_settings.html", {"form": form, "setting": setting})


def _error_context(request, status_code, title, message):
    user = getattr(request, "user", None)
    if user and user.is_authenticated and is_cashier_user(user) and not is_admin_user(user):
        action_label = "Back to POS"
        action_url = reverse("pos-sale")
        secondary_label = "Login again"
        secondary_url = reverse("dashboard-login")
    elif user and user.is_authenticated and can_access_dashboard(user):
        action_label = "Back to Dashboard"
        action_url = reverse("dashboard-home")
        secondary_label = "Login again"
        secondary_url = reverse("dashboard-login")
    else:
        action_label = "Login again"
        action_url = reverse("dashboard-login")
        secondary_label = ""
        secondary_url = ""

    return {
        "status_code": status_code,
        "title": title,
        "message": message,
        "action_label": action_label,
        "action_url": action_url,
        "secondary_label": secondary_label,
        "secondary_url": secondary_url,
    }


def dashboard_permission_denied_view(request, exception=None):
    return render(
        request,
        "dashboard/error.html",
        _error_context(
            request,
            "403",
            "Access denied",
            "Your account does not have permission to open this area.",
        ),
        status=403,
    )


def dashboard_page_not_found_view(request, exception=None):
    return render(
        request,
        "dashboard/error.html",
        _error_context(
            request,
            "404",
            "Page or item not found",
            "The page or record you requested could not be found.",
        ),
        status=404,
    )


def dashboard_server_error_view(request):
    return render(
        request,
        "dashboard/error.html",
        _error_context(
            request,
            "500",
            "Unexpected error",
            "Something went wrong while handling the request.",
        ),
        status=500,
    )


def health_check(request):
    status_code = 200
    payload = {
        "service": "Melodu POS & Inventory Control System",
        "status": "ok",
        "database": "ok",
        "migrations": "ok",
    }

    try:
        connection = connections["default"]
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()

        executor = MigrationExecutor(connection)
        unapplied = executor.migration_plan(executor.loader.graph.leaf_nodes())
        if unapplied:
            payload["status"] = "degraded"
            payload["migrations"] = "unapplied"
            payload["unapplied_migration_count"] = len(unapplied)
            payload["unapplied_migrations"] = [
                f"{migration.app_label}.{migration.name}" for migration, _backwards in unapplied[:20]
            ]
            status_code = 503
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


@dashboard_required
def dashboard_home_view(request):
    """Role-aware home.

    The home page is driven by capabilities rather than a single admin flag so
    every role lands on a page made of areas they can actually open. Inventory
    staff and Viewers must never be shown POS shortcuts (they cannot access POS
    and would hit a 403).
    """
    user = request.user
    today = timezone.localdate()

    caps = {
        "is_admin": is_admin_user(user),
        "can_pos": can_access_pos(user),
        "can_inventory": can_manage_inventory(user),
        "can_catalog": can_manage_catalog(user),
        "can_reports": can_view_reports(user),
        "can_sales_history": can_view_sales_history(user),
    }

    stats = {}
    recent_sales = []
    recent_uploads = []

    if caps["can_inventory"]:
        stats["products"] = Product.objects.filter(is_active=True).count()
        stats["active_batches"] = StockBatch.objects.filter(status=StockBatch.Status.ACTIVE).count()
        stats["low_stock_products"] = (
            Product.objects.filter(stock_batches__isnull=False)
            .annotate(total_available=Sum("stock_batches__quantity_available"))
            .filter(total_available__lte=F("min_stock"))
            .distinct()
            .count()
        )

    if caps["can_sales_history"]:
        # Owner/Manager/Viewer see store-wide sales activity (read-only for Viewer).
        stats["today_sales"] = Sale.objects.filter(created_at__date=today).count()
        recent_sales = Sale.objects.select_related("cashier").order_by("-created_at")[:5]
    elif caps["can_pos"]:
        # Cashier sees only their own activity.
        stats["today_sales"] = Sale.objects.filter(cashier=user, created_at__date=today).count()
        stats["cart_ready"] = 1
        recent_sales = Sale.objects.filter(cashier=user).order_by("-created_at")[:5]

    if caps["can_catalog"]:
        recent_uploads = BatchUploadJob.objects.select_related("uploaded_by").order_by("-created_at")[:5]

    context = {
        "today": today,
        "caps": caps,
        "stats": stats,
        "recent_sales": recent_sales,
        "recent_uploads": recent_uploads,
    }
    return render(request, "dashboard/home.html", context)


@require_GET
@dashboard_required
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
