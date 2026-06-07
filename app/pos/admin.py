from django.contrib import admin

from .models import Sale, SaleItem


class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0
    can_delete = False
    readonly_fields = ("product", "stock_batch", "quantity", "unit_price", "subtotal", "created_at")

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = (
        "sale_no",
        "cashier",
        "total_amount",
        "discount_amount",
        "final_amount",
        "payment_method",
        "status",
        "created_at",
    )
    list_filter = ("status", "payment_method", "created_at")
    search_fields = ("sale_no", "cashier__username", "items__product__name", "items__stock_batch__batch_no")
    readonly_fields = (
        "sale_no",
        "cashier",
        "total_amount",
        "discount_amount",
        "final_amount",
        "payment_method",
        "status",
        "cancel_reason",
        "created_at",
        "updated_at",
    )
    inlines = [SaleItemInline]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(SaleItem)
class SaleItemAdmin(admin.ModelAdmin):
    list_display = ("sale", "product", "stock_batch", "quantity", "unit_price", "subtotal", "created_at")
    list_filter = ("created_at",)
    search_fields = ("sale__sale_no", "product__name", "stock_batch__batch_no")
    readonly_fields = [field.name for field in SaleItem._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
