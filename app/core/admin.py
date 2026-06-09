from django.contrib import admin

from .models import StoreSetting


@admin.register(StoreSetting)
class StoreSettingAdmin(admin.ModelAdmin):
    list_display = ("store_name", "receipt_paper_width_mm", "updated_at")
    readonly_fields = ("created_at", "updated_at")

    def has_add_permission(self, request):
        # Singleton: only one row is ever used.
        return not StoreSetting.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
