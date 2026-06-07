import os
import shutil
from pathlib import Path

from django.conf import settings
from django.db import connections
from django.shortcuts import render

from core.permissions import admin_required
from inventory.models import StockBatch
from pos.models import Sale


def redact_log_line(line):
    redacted = line
    sensitive_values = [settings.SECRET_KEY]
    for key, value in os.environ.items():
        if any(marker in key.upper() for marker in ("SECRET", "PASSWORD", "TOKEN", "KEY")) and value:
            sensitive_values.append(value)
    for value in sensitive_values:
        if value and len(value) >= 4:
            redacted = redacted.replace(value, "[REDACTED]")
    return redacted


def read_latest_log_lines(path, limit=100):
    path = Path(path)
    if not path.exists():
        return []
    lines = path.read_text(errors="replace").splitlines()
    return [redact_log_line(line) for line in reversed(lines[-limit:]) if line.strip()]


def check_database_status():
    try:
        with connections["default"].cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception as exc:
        return f"error: {exc.__class__.__name__}"
    return "ok"


def check_log_writable():
    try:
        settings.LOG_DIR.mkdir(parents=True, exist_ok=True)
        probe = settings.LOG_DIR / ".write-check"
        probe.write_text("ok")
        probe.unlink(missing_ok=True)
    except Exception as exc:
        return f"error: {exc.__class__.__name__}"
    return "ok"


def get_disk_usage_path():
    for path in (settings.DATA_ROOT, settings.LOG_DIR, settings.MEDIA_ROOT, settings.STATIC_ROOT, settings.BASE_DIR):
        if Path(path).exists():
            return path
    return Path("/")


@admin_required
def live_logs_view(request):
    app_log = settings.LOG_DIR / "app.log"
    error_log = settings.LOG_DIR / "error.log"
    return render(
        request,
        "system_logs/live_logs.html",
        {
            "app_lines": read_latest_log_lines(app_log),
            "error_lines": read_latest_log_lines(error_log),
        },
    )


@admin_required
def system_health_view(request):
    disk = shutil.disk_usage(get_disk_usage_path())
    latest_sale = Sale.objects.order_by("-created_at").first()
    latest_stock_in = StockBatch.objects.order_by("-received_at").first()
    latest_error_lines = read_latest_log_lines(settings.LOG_DIR / "error.log", limit=1)
    context = {
        "database_status": check_database_status(),
        "app_version": settings.APP_VERSION,
        "disk_total": disk.total,
        "disk_used": disk.used,
        "disk_free": disk.free,
        "log_writable_status": check_log_writable(),
        "last_sale_time": latest_sale.created_at if latest_sale else None,
        "last_stock_in_time": latest_stock_in.received_at if latest_stock_in else None,
        "last_error": latest_error_lines[0] if latest_error_lines else "",
    }
    return render(request, "system_logs/system_health.html", context)
