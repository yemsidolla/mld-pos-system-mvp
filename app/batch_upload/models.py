from django.conf import settings
from django.db import models
from django.utils import timezone


class BatchUploadJob(models.Model):
    class Target(models.TextChoices):
        CATEGORIES = "categories", "Categories"
        BRANDS = "brands", "Brands"
        SUPPLIERS = "suppliers", "Suppliers"
        PRODUCTS = "products", "Products"
        STOCK_IN = "stock_in", "Stock-In"

    class Status(models.TextChoices):
        PREVIEW = "PREVIEW", "Preview"
        COMMITTED = "COMMITTED", "Committed"

    target = models.CharField(max_length=40, choices=Target.choices)
    original_filename = models.CharField(max_length=255)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="batch_upload_jobs",
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PREVIEW)
    summary = models.JSONField(default=dict, blank=True)
    committed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["target", "status"]),
            models.Index(fields=["uploaded_by", "created_at"]),
        ]

    def __str__(self):
        return f"{self.get_target_display()} upload #{self.pk}"

    def mark_committed(self, summary):
        self.status = self.Status.COMMITTED
        self.summary = summary
        self.committed_at = timezone.now()
        self.save(update_fields=["status", "summary", "committed_at", "updated_at"])


class BatchUploadRow(models.Model):
    job = models.ForeignKey(BatchUploadJob, on_delete=models.CASCADE, related_name="rows")
    row_number = models.PositiveIntegerField()
    raw_data = models.JSONField(default=dict)
    normalized_data = models.JSONField(default=dict)
    validation_errors = models.JSONField(default=list, blank=True)
    warnings = models.JSONField(default=list, blank=True)
    is_selected = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    committed_action = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["row_number", "id"]
        constraints = [
            models.UniqueConstraint(fields=["job", "row_number"], name="unique_batch_upload_job_row_number"),
        ]

    def __str__(self):
        return f"{self.job_id} row {self.row_number}"

    @property
    def can_commit(self):
        return self.is_selected and not self.is_deleted and not self.validation_errors
