from django.contrib import admin

from .models import LabelTemplate


@admin.register(LabelTemplate)
class LabelTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "template_type", "paper_width_mm", "paper_height_mm", "is_default", "is_active")
    list_filter = ("template_type", "is_active", "is_default")
    search_fields = ("name",)
    readonly_fields = ("created_at", "updated_at")
