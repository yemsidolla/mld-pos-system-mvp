from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    class Action(models.TextChoices):
        LOGIN_SUCCESS = "LOGIN_SUCCESS", "Login success"
        LOGIN_FAILED = "LOGIN_FAILED", "Login failed"
        CREATE = "CREATE", "Create"
        UPDATE = "UPDATE", "Update"
        DELETE = "DELETE", "Delete"
        DEACTIVATE = "DEACTIVATE", "Deactivate"
        STOCK_IN = "STOCK_IN", "Stock in"
        STOCK_ADJUSTMENT = "STOCK_ADJUSTMENT", "Stock adjustment"
        SALE_CREATE = "SALE_CREATE", "Sale create"
        SALE_CANCEL = "SALE_CANCEL", "Sale cancel"
        REFUND = "REFUND", "Refund"
        BARCODE_GENERATE = "BARCODE_GENERATE", "Barcode generate"
        BARCODE_PRINT = "BARCODE_PRINT", "Barcode print"
        ROLE_CHANGE = "ROLE_CHANGE", "Role change"
        SETTING_CHANGE = "SETTING_CHANGE", "Setting change"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    action = models.CharField(max_length=40, choices=Action.choices)
    module = models.CharField(max_length=80)
    object_type = models.CharField(max_length=120, blank=True)
    object_id = models.CharField(max_length=80, blank=True)
    object_display = models.CharField(max_length=255, blank=True)
    old_value = models.JSONField(null=True, blank=True)
    new_value = models.JSONField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["action", "created_at"]),
            models.Index(fields=["module", "created_at"]),
            models.Index(fields=["object_type", "object_id"]),
        ]

    def __str__(self):
        return f"{self.action} {self.module} {self.created_at:%Y-%m-%d %H:%M:%S}"
