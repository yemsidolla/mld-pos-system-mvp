from django.contrib import admin

from .forms import ProductForm
from .models import AnimalTypeOption, Brand, Category, Product, ProductTag, Supplier, SupplierProductCost


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


@admin.register(ProductTag)
class ProductTagAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("name",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(AnimalTypeOption)
class AnimalTypeOptionAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("name", "code")
    readonly_fields = ("created_at", "updated_at")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    # Same processing path as the dashboard ProductForm (WebP original + thumb).
    form = ProductForm
    list_display = (
        "product_code",
        "name",
        "original_barcode",
        "category",
        "brand",
        "animal_type_list",
        "life_stage",
        "default_selling_price",
        "min_stock",
        "is_active",
    )
    list_filter = ("is_active", "category", "brand", "animal_types", "life_stage", "tags")
    search_fields = ("name", "product_code", "original_barcode")
    # image_thumb is derived — never editable into an inconsistent state (F7).
    readonly_fields = ("image_thumb", "created_at", "updated_at")
    autocomplete_fields = ("category", "brand")
    filter_horizontal = ("animal_types", "tags")

    @admin.display(description="Animal types")
    def animal_type_list(self, obj):
        return ", ".join(obj.animal_type_labels) or "-"


@admin.register(SupplierProductCost)
class SupplierProductCostAdmin(admin.ModelAdmin):
    list_display = ("product", "supplier", "reference_unit_cost", "is_active", "updated_at")
    list_filter = ("is_active", "supplier")
    search_fields = ("product__name", "product__product_code", "supplier__name")
    autocomplete_fields = ("product", "supplier")
    readonly_fields = ("created_at", "updated_at")
