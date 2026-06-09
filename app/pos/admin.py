from django.contrib import admin

from .models import Promotion, Sale, SaleItem


class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0
    can_delete = False
    readonly_fields = (
        "product",
        "stock_batch",
        "quantity",
        "unit_price",
        "cost_basis_at_sale",
        "original_unit_price",
        "final_unit_price",
        "discount_amount",
        "promotion_name_at_sale",
        "override_by",
        "override_reason",
        "subtotal",
        "created_at",
    )

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
    list_display = ("sale", "product", "stock_batch", "quantity", "final_unit_price", "cost_basis_at_sale", "subtotal", "created_at")
    list_filter = ("created_at", "promotion")
    search_fields = ("sale__sale_no", "product__name", "stock_batch__batch_no")
    readonly_fields = [field.name for field in SaleItem._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "discount_type",
        "value",
        "start_date",
        "end_date",
        "is_active",
        "allow_below_cost",
        "product",
        "category",
    )
    list_filter = ("is_active", "discount_type", "allow_below_cost", "start_date", "end_date")
    search_fields = ("name", "product__name", "product__product_code", "category__name")
    autocomplete_fields = ("product", "category", "created_by")
    readonly_fields = ("created_at", "updated_at")
