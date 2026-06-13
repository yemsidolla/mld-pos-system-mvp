from django.conf import settings

from .models import StoreSetting
from .permissions import (
    can_access_pos,
    can_manage_catalog,
    can_manage_inventory,
    can_manage_promotions,
    can_manage_settings,
    can_manage_users,
    can_view_audit,
    can_view_costs,
    can_view_reports,
    can_view_sales_history,
    can_view_system,
    get_user_role,
    is_admin_user,
    is_owner,
    is_cashier_user,
    role_label,
)


def dashboard_context(request):
    user = getattr(request, "user", None)
    role = get_user_role(user) if user else None
    is_admin = bool(user and is_admin_user(user))
    is_cashier = bool(user and is_cashier_user(user))

    nav_groups = []

    overview_items = []
    if role is not None:
        overview_items.append({"label": "Dashboard", "icon": "home", "url_name": "dashboard-home", "href": "/dashboard/"})
    if overview_items:
        nav_groups.append({"label": "Overview", "items": overview_items})

    sales_items = []
    if user and can_access_pos(user):
        sales_items.append({"label": "POS", "icon": "cart", "url_name": "pos-sale", "href": "/dashboard/pos/"})
    if user and can_view_sales_history(user):
        sales_items.append({"label": "Sales History", "icon": "receipt", "url_name": "sales-history", "href": "/dashboard/sales/"})
    if sales_items:
        nav_groups.append({"label": "Sales", "items": sales_items})

    user_sees_costs = bool(user and can_view_costs(user))

    catalog_items = []
    if user and can_manage_catalog(user):
        catalog_items.extend(
            [
                {"label": "Products", "icon": "package", "url_name": "product-list", "href": "/dashboard/products/"},
                {"label": "Categories", "icon": "category", "url_name": "category-list", "href": "/dashboard/categories/"},
                {"label": "Brands", "icon": "tag", "url_name": "brand-list", "href": "/dashboard/brands/"},
                {"label": "Suppliers", "icon": "users", "url_name": "supplier-list", "href": "/dashboard/suppliers/"},
            ]
        )
        if user_sees_costs:
            catalog_items.append(
                {"label": "Reference Costs", "icon": "dollar", "url_name": "supplier-product-cost-list", "href": "/dashboard/reference-costs/"}
            )
    if user and can_manage_promotions(user):
        catalog_items.append({"label": "Promotions", "icon": "percent", "url_name": "promotion-list", "href": "/dashboard/promotions/"})
    if user and can_manage_catalog(user):
        catalog_items.append(
            {"label": "Label Templates", "icon": "printer", "url_name": "label-template-list", "href": "/dashboard/labels/templates/"}
        )
        catalog_items.append({"label": "Batch Upload", "icon": "upload", "url_name": "batch-upload", "href": "/dashboard/batch-upload/"})
    if catalog_items:
        nav_groups.append({"label": "Catalog", "items": catalog_items})

    inventory_items = []
    if user and can_manage_inventory(user):
        inventory_items.append({"label": "Receive Stock", "icon": "truck", "url_name": "stock-in", "href": "/dashboard/stock-in/"})
        inventory_items.append({"label": "Stock Overview", "icon": "package", "url_name": "inventory-summary", "href": "/dashboard/inventory/"})
        inventory_items.append(
            {"label": "Barcode / QR Print", "icon": "barcode", "url_name": "barcode-print", "href": "/dashboard/barcode-print/"}
        )
        inventory_items.append({"label": "Print Labels", "icon": "printer", "url_name": "label-print", "href": "/dashboard/labels/print/"})
        inventory_items.append(
            {"label": "Promotion Labels", "icon": "percent", "url_name": "promotion-label-print", "href": "/dashboard/labels/promotions/"}
        )
    if inventory_items:
        nav_groups.append({"label": "Inventory", "items": inventory_items})

    reports_items = []
    if user and can_view_reports(user):
        reports_items.append({"label": "Reports", "icon": "chart", "url_name": "reports-index", "href": "/dashboard/reports/"})
    if reports_items:
        nav_groups.append({"label": "Reports", "items": reports_items})

    admin_items = []
    if user and can_manage_users(user):
        admin_items.append({"label": "Users", "icon": "user", "url_name": "user-list", "href": "/dashboard/users/"})
    if user and can_manage_settings(user):
        admin_items.append({"label": "Settings", "icon": "settings", "url_name": "store-settings", "href": "/dashboard/settings/"})
    if user and can_view_audit(user):
        admin_items.append({"label": "Audit Logs", "icon": "shield", "url_name": "audit-log-list", "href": "/dashboard/audit-logs/"})
    if user and can_view_system(user):
        admin_items.append({"label": "System Health", "icon": "activity", "url_name": "system-health", "href": "/dashboard/system-health/"})
        admin_items.append({"label": "Live Logs", "icon": "logs", "url_name": "live-logs", "href": "/dashboard/live-logs/"})
    if user and is_owner(user):
        admin_items.append({"label": "Role Permissions", "icon": "shield", "url_name": "role-matrix", "href": "/dashboard/roles/"})
    if is_admin:
        admin_items.append({"label": "Styleguide", "icon": "category", "url_name": "styleguide", "href": "/dashboard/styleguide/"})
    if admin_items:
        nav_groups.append({"label": "Administration", "items": admin_items})

    nav_items = [item for group in nav_groups for item in group["items"]]

    # Mobile bottom nav: a curated, role-weighted set of the most-used
    # destinations (max 5), rather than the first five sidebar items. Built from
    # the already-computed capability flags so it always matches access.
    by_url = {item["url_name"]: item for item in nav_items}
    mobile_priority = [
        "dashboard-home",
        "pos-sale",
        "inventory-summary",
        "product-list",
        "sales-history",
        "reports-index",
        "stock-in",
    ]
    mobile_nav_items = [by_url[name] for name in mobile_priority if name in by_url][:5]

    try:
        store_setting = StoreSetting.load()
    except Exception:  # pragma: no cover - defensive (e.g. before migrations)
        store_setting = None

    return {
        "app_version": getattr(settings, "APP_VERSION", "dev"),
        "dashboard_nav_groups": nav_groups,
        "dashboard_nav_items": nav_items,
        "dashboard_mobile_nav_items": mobile_nav_items,
        "dashboard_is_admin": is_admin,
        "dashboard_is_cashier": is_cashier,
        "dashboard_role": role,
        "dashboard_role_label": role_label(role) if role else "",
        "dashboard_can_view_costs": user_sees_costs,
        "store_setting": store_setting,
        "supported_languages": settings.LANGUAGES,
    }
