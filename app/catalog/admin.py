from django.contrib import admin

from .models import Brand, Category, Product, Supplier


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "created_at", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("name", "description")
    readonly_fields = ("created_at", "updated_at")


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "created_at", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("name", "description")
    readonly_fields = ("created_at", "updated_at")


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ("name", "contact_person", "phone", "telegram", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "contact_person", "phone", "telegram")
    readonly_fields = ("created_at", "updated_at")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "product_code",
        "name",
        "original_barcode",
        "category",
        "brand",
        "default_selling_price",
        "min_stock",
        "is_active",
    )
    list_filter = ("is_active", "category", "brand")
    search_fields = ("name", "product_code", "original_barcode")
    readonly_fields = ("created_at", "updated_at")
    autocomplete_fields = ("category", "brand")
