"""URL configuration for Melodu POS."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from batch_upload.views import (
    batch_upload_commit_view,
    batch_upload_detail_view,
    batch_upload_index_view,
    batch_upload_row_delete_view,
    batch_upload_row_update_view,
    batch_upload_template_view,
)
from catalog.views import (
    brand_create_view,
    brand_edit_view,
    brand_list_view,
    category_create_view,
    category_edit_view,
    category_list_view,
    product_create_view,
    product_edit_view,
    product_list_view,
    supplier_create_view,
    supplier_edit_view,
    supplier_list_view,
)
from core.views import dashboard_home_view, health_check, scan_resolve_view
from inventory.views import barcode_print_view, inventory_summary_view, stock_batch_detail_view, stock_in_view
from pos.views import pos_sale_view, sale_cancel_view, sale_detail_view, sale_receipt_view, sales_history_view
from reports.views import (
    daily_sales_report_view,
    expiry_report_view,
    low_stock_report_view,
    reports_index_view,
    staff_sales_report_view,
    stock_movement_report_view,
    stock_summary_report_view,
)
from system_logs.views import live_logs_view, system_health_view


urlpatterns = [
    path("admin/", admin.site.urls),
    path("i18n/", include("django.conf.urls.i18n")),
    path("dashboard/", dashboard_home_view, name="dashboard-home"),
    path("dashboard/api/scan/resolve/", scan_resolve_view, name="scan-resolve"),
    path("dashboard/products/", product_list_view, name="product-list"),
    path("dashboard/products/new/", product_create_view, name="product-create"),
    path("dashboard/products/<int:product_id>/edit/", product_edit_view, name="product-edit"),
    path("dashboard/categories/", category_list_view, name="category-list"),
    path("dashboard/categories/new/", category_create_view, name="category-create"),
    path("dashboard/categories/<int:category_id>/edit/", category_edit_view, name="category-edit"),
    path("dashboard/brands/", brand_list_view, name="brand-list"),
    path("dashboard/brands/new/", brand_create_view, name="brand-create"),
    path("dashboard/brands/<int:brand_id>/edit/", brand_edit_view, name="brand-edit"),
    path("dashboard/suppliers/", supplier_list_view, name="supplier-list"),
    path("dashboard/suppliers/new/", supplier_create_view, name="supplier-create"),
    path("dashboard/suppliers/<int:supplier_id>/edit/", supplier_edit_view, name="supplier-edit"),
    path("dashboard/batch-upload/", batch_upload_index_view, name="batch-upload"),
    path("dashboard/batch-upload/templates/<str:target>/", batch_upload_template_view, name="batch-upload-template"),
    path("dashboard/batch-upload/jobs/<int:job_id>/", batch_upload_detail_view, name="batch-upload-detail"),
    path("dashboard/batch-upload/jobs/<int:job_id>/commit/", batch_upload_commit_view, name="batch-upload-commit"),
    path(
        "dashboard/batch-upload/jobs/<int:job_id>/rows/<int:row_id>/update/",
        batch_upload_row_update_view,
        name="batch-upload-row-update",
    ),
    path(
        "dashboard/batch-upload/jobs/<int:job_id>/rows/<int:row_id>/delete/",
        batch_upload_row_delete_view,
        name="batch-upload-row-delete",
    ),
    path("dashboard/barcode-print/", barcode_print_view, name="barcode-print"),
    path("dashboard/inventory/", inventory_summary_view, name="inventory-summary"),
    path("dashboard/inventory/batches/<int:batch_id>/", stock_batch_detail_view, name="stock-batch-detail"),
    path("dashboard/pos/", pos_sale_view, name="pos-sale"),
    path("dashboard/pos/receipt/<int:sale_id>/", sale_receipt_view, name="sale-receipt"),
    path("dashboard/reports/", reports_index_view, name="reports-index"),
    path("dashboard/reports/daily-sales/", daily_sales_report_view, name="daily-sales-report"),
    path("dashboard/reports/stock-summary/", stock_summary_report_view, name="stock-summary-report"),
    path("dashboard/reports/low-stock/", low_stock_report_view, name="low-stock-report"),
    path("dashboard/reports/expiry/", expiry_report_view, name="expiry-report"),
    path("dashboard/reports/stock-movements/", stock_movement_report_view, name="stock-movement-report"),
    path("dashboard/reports/staff-sales/", staff_sales_report_view, name="staff-sales-report"),
    path("dashboard/sales/", sales_history_view, name="sales-history"),
    path("dashboard/sales/<int:sale_id>/", sale_detail_view, name="sale-detail"),
    path("dashboard/sales/<int:sale_id>/cancel/", sale_cancel_view, name="sale-cancel"),
    path("dashboard/live-logs/", live_logs_view, name="live-logs"),
    path("dashboard/system-health/", system_health_view, name="system-health"),
    path("dashboard/stock-in/", stock_in_view, name="stock-in"),
    path("health/", health_check, name="health-check"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
