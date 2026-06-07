from django.contrib import admin

from .models import InventoryMovement, StockBatch


@admin.register(StockBatch)
class StockBatchAdmin(admin.ModelAdmin):
    list_display = (
        "batch_no",
        "product",
        "supplier",
        "expiry_date",
        "quantity_received",
        "quantity_available",
        "selling_price",
        "status",
        "received_by",
        "received_at",
    )
    list_filter = ("status", "supplier", "expiry_date")
    search_fields = ("batch_no", "custom_code", "product__name", "product__product_code", "product__original_barcode")
    autocomplete_fields = ("product", "supplier", "received_by")
    readonly_fields = (
        "batch_no",
        "custom_code",
        "barcode_image",
        "qr_image",
        "received_at",
        "created_at",
        "updated_at",
    )

    def has_add_permission(self, request):
        return False


@admin.register(InventoryMovement)
class InventoryMovementAdmin(admin.ModelAdmin):
    list_display = (
        "created_at",
        "movement_type",
        "product",
        "stock_batch",
        "quantity",
        "reference_type",
        "reference_id",
        "created_by",
    )
    list_filter = ("movement_type", "created_at")
    search_fields = ("product__name", "stock_batch__batch_no", "reference_type", "reference_id", "note")
    readonly_fields = [field.name for field in InventoryMovement._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return request.user.is_active and request.user.is_staff

    def has_delete_permission(self, request, obj=None):
        return False
