from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = (
        "created_at",
        "action",
        "module",
        "user",
        "object_type",
        "object_display",
        "ip_address",
    )
    list_filter = ("action", "module", "created_at")
    search_fields = ("user__username", "object_type", "object_id", "object_display", "ip_address")
    date_hierarchy = "created_at"
    readonly_fields = (
        "user",
        "action",
        "module",
        "object_type",
        "object_id",
        "object_display",
        "old_value",
        "new_value",
        "ip_address",
        "user_agent",
        "created_at",
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_readonly_fields(self, request, obj=None):
        return [field.name for field in self.model._meta.fields]
