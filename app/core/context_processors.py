from django.conf import settings

from .permissions import can_access_pos, is_admin_user, is_cashier_user


def dashboard_context(request):
    user = getattr(request, "user", None)
    is_admin = bool(user and is_admin_user(user))
    is_cashier = bool(user and is_cashier_user(user))
    nav_items = []

    if user and user.is_authenticated and can_access_pos(user):
        nav_items.append({"label": "Dashboard", "url_name": "dashboard-home", "href": "/dashboard/"})
        nav_items.append({"label": "POS", "url_name": "pos-sale", "href": "/dashboard/pos/"})

    if is_admin:
        nav_items.extend(
            [
                {"label": "Stock-In", "url_name": "stock-in", "href": "/dashboard/stock-in/"},
                {"label": "Products", "url_name": "product-list", "href": "/dashboard/products/"},
                {"label": "Inventory", "url_name": "inventory-summary", "href": "/dashboard/inventory/"},
                {"label": "Batch Upload", "url_name": "batch-upload", "href": "/dashboard/batch-upload/"},
                {"label": "Labels", "url_name": "barcode-print", "href": "/dashboard/barcode-print/"},
                {"label": "Sales", "url_name": "sales-history", "href": "/dashboard/sales/"},
                {"label": "Reports", "url_name": "reports-index", "href": "/dashboard/reports/"},
                {"label": "System", "url_name": "system-health", "href": "/dashboard/system-health/"},
            ]
        )

    return {
        "app_version": getattr(settings, "APP_VERSION", "dev"),
        "dashboard_nav_items": nav_items,
        "dashboard_is_admin": is_admin,
        "dashboard_is_cashier": is_cashier,
        "supported_languages": settings.LANGUAGES,
    }
