import os
import shutil
from pathlib import Path

from django.conf import settings
from django.db import connections
from django.shortcuts import render

from core.permissions import system_required
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


def format_bytes(value):
    size = float(value)
    units = ("B", "KB", "MB", "GB", "TB")
    for unit in units:
        if size < 1024 or unit == units[-1]:
            if unit == "B":
                return f"{int(size)} {unit}"
            return f"{size:.1f} {unit}"
        size /= 1024


@system_required
def live_logs_view(request):
    app_log = settings.LOG_DIR / "app.log"
    error_log = settings.LOG_DIR / "error.log"
    app_lines = read_latest_log_lines(app_log)
    error_lines = read_latest_log_lines(error_log)
    return render(
        request,
        "system_logs/live_logs.html",
        {
            "app_lines": app_lines,
            "error_lines": error_lines,
            "app_line_count": len(app_lines),
            "error_line_count": len(error_lines),
        },
    )


@system_required
def system_health_view(request):
    disk = shutil.disk_usage(get_disk_usage_path())
    database_status = check_database_status()
    log_writable_status = check_log_writable()
    latest_sale = Sale.objects.order_by("-created_at").first()
    latest_stock_in = StockBatch.objects.order_by("-received_at").first()
    latest_error_lines = read_latest_log_lines(settings.LOG_DIR / "error.log", limit=1)
    disk_used_percent = round((disk.used / disk.total) * 100, 1) if disk.total else 0
    if disk_used_percent >= 90:
        disk_status = "critical"
    elif disk_used_percent >= 80:
        disk_status = "warning"
    else:
        disk_status = "ok"
    if database_status != "ok" or log_writable_status != "ok" or disk_status == "critical":
        overall_status = "Attention"
        overall_badge_class = "badge-danger"
    elif latest_error_lines or disk_status == "warning":
        overall_status = "Review"
        overall_badge_class = "badge-warning"
    else:
        overall_status = "OK"
        overall_badge_class = "badge-success"
    context = {
        "overall_status": overall_status,
        "overall_badge_class": overall_badge_class,
        "database_status": database_status,
        "database_ok": database_status == "ok",
        "app_version": settings.APP_VERSION,
        "disk_total": disk.total,
        "disk_total_display": format_bytes(disk.total),
        "disk_used": disk.used,
        "disk_used_display": format_bytes(disk.used),
        "disk_free": disk.free,
        "disk_free_display": format_bytes(disk.free),
        "disk_used_percent": disk_used_percent,
        "disk_status": disk_status,
        "log_writable_status": log_writable_status,
        "log_writable_ok": log_writable_status == "ok",
        "last_sale_time": latest_sale.created_at if latest_sale else None,
        "last_stock_in_time": latest_stock_in.received_at if latest_stock_in else None,
        "last_error": latest_error_lines[0] if latest_error_lines else "",
        "backup_docs": [
            "docs/guides/BACKUP_GUIDE.md",
            "docs/guides/MINIO_STORAGE_GUIDE.md",
            "docs/operations/DEPLOYMENT_RUNBOOK.md",
            "docs/operations/RESET_ADMIN_RUNBOOK.md",
        ],
        "backup_commands": [
            "scripts/backup_db.sh",
            "scripts/backup_media.sh",
            "scripts/backup_minio.sh",
        ],
    }
    return render(request, "system_logs/system_health.html", context)
