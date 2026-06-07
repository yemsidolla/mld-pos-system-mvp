from django.contrib import admin

from .models import BatchUploadJob, BatchUploadRow


class BatchUploadRowInline(admin.TabularInline):
    model = BatchUploadRow
    extra = 0
    can_delete = False
    readonly_fields = (
        "row_number",
        "raw_data",
        "normalized_data",
        "validation_errors",
        "warnings",
        "is_selected",
        "is_deleted",
        "committed_action",
        "created_at",
        "updated_at",
    )

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(BatchUploadJob)
class BatchUploadJobAdmin(admin.ModelAdmin):
    list_display = ("id", "target", "status", "original_filename", "uploaded_by", "created_at", "committed_at")
    list_filter = ("target", "status", "created_at")
    search_fields = ("original_filename", "uploaded_by__username")
    readonly_fields = ("summary", "created_at", "updated_at", "committed_at")
    inlines = [BatchUploadRowInline]


@admin.register(BatchUploadRow)
class BatchUploadRowAdmin(admin.ModelAdmin):
    list_display = ("job", "row_number", "is_selected", "is_deleted", "committed_action")
    list_filter = ("job__target", "is_selected", "is_deleted", "committed_action")
    search_fields = ("job__original_filename",)
    readonly_fields = ("created_at", "updated_at")
