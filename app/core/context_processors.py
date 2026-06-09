from django.conf import settings

from .models import StoreSetting
from .permissions import (
    can_access_pos,
    can_manage_catalog,
    can_manage_inventory,
    can_manage_promotions,
    can_manage_settings,
    can_manage_users,
    can_view_reports,
    can_view_sales_history,
    can_view_system,
    get_user_role,
    is_admin_user,
    is_cashier_user,
    role_label,
)


def dashboard_context(request):
    user = getattr(request, "user", None)
    role = get_user_role(user) if user else None
    is_admin = bool(user and is_admin_user(user))
    is_cashier = bool(user and is_cashier_user(user))
    nav_items = []

    if role is not None:
        nav_items.append({"label": "Dashboard", "url_name": "dashboard-home", "href": "/dashboard/"})
    if user and can_access_pos(user):
        nav_items.append({"label": "POS", "url_name": "pos-sale", "href": "/dashboard/pos/"})
    if user and can_manage_inventory(user):
        nav_items.append({"label": "Stock-In", "url_name": "stock-in", "href": "/dashboard/stock-in/"})
    if user and can_manage_catalog(user):
        nav_items.extend(
            [
                {"label": "Products", "url_name": "product-list", "href": "/dashboard/products/"},
                {"label": "Categories", "url_name": "category-list", "href": "/dashboard/categories/"},
                {"label": "Brands", "url_name": "brand-list", "href": "/dashboard/brands/"},
                {"label": "Suppliers", "url_name": "supplier-list", "href": "/dashboard/suppliers/"},
                {"label": "Costs", "url_name": "supplier-product-cost-list", "href": "/dashboard/reference-costs/"},
            ]
        )
    if user and can_manage_promotions(user):
        nav_items.append({"label": "Promotions", "url_name": "promotion-list", "href": "/dashboard/promotions/"})
    if user and can_manage_inventory(user):
        nav_items.append({"label": "Inventory", "url_name": "inventory-summary", "href": "/dashboard/inventory/"})
    if user and can_manage_catalog(user):
        nav_items.append({"label": "Batch Upload", "url_name": "batch-upload", "href": "/dashboard/batch-upload/"})
    if user and can_manage_inventory(user):
        nav_items.append({"label": "Labels", "url_name": "barcode-print", "href": "/dashboard/barcode-print/"})
        nav_items.append({"label": "Print Labels", "url_name": "label-print", "href": "/dashboard/labels/print/"})
    if user and can_manage_catalog(user):
        nav_items.append(
            {"label": "Label Templates", "url_name": "label-template-list", "href": "/dashboard/labels/templates/"}
        )
    if user and can_view_sales_history(user):
        nav_items.append({"label": "Sales", "url_name": "sales-history", "href": "/dashboard/sales/"})
    if user and can_view_reports(user):
        nav_items.append({"label": "Reports", "url_name": "reports-index", "href": "/dashboard/reports/"})
    if user and can_manage_users(user):
        nav_items.append({"label": "Users", "url_name": "user-list", "href": "/dashboard/users/"})
    if user and can_manage_settings(user):
        nav_items.append({"label": "Settings", "url_name": "store-settings", "href": "/dashboard/settings/"})
    if user and can_view_system(user):
        nav_items.append({"label": "System", "url_name": "system-health", "href": "/dashboard/system-health/"})

    try:
        store_setting = StoreSetting.load()
    except Exception:  # pragma: no cover - defensive (e.g. before migrations)
        store_setting = None

    return {
        "app_version": getattr(settings, "APP_VERSION", "dev"),
        "dashboard_nav_items": nav_items,
        "dashboard_is_admin": is_admin,
        "dashboard_is_cashier": is_cashier,
        "dashboard_role": role,
        "dashboard_role_label": role_label(role) if role else "",
        "store_setting": store_setting,
        "supported_languages": settings.LANGUAGES,
    }
