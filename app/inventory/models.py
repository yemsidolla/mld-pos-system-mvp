from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone


class StockBatch(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        SOLD_OUT = "SOLD_OUT", "Sold out"
        EXPIRED = "EXPIRED", "Expired"
        DAMAGED = "DAMAGED", "Damaged"
        LOCKED = "LOCKED", "Locked"

    product = models.ForeignKey("catalog.Product", on_delete=models.PROTECT, related_name="stock_batches")
    supplier = models.ForeignKey("catalog.Supplier", on_delete=models.PROTECT, related_name="stock_batches")
    batch_no = models.CharField(max_length=20, unique=True)
    expiry_date = models.DateField()
    quantity_received = models.PositiveIntegerField()
    quantity_available = models.PositiveIntegerField()
    actual_unit_cost = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    landed_unit_cost = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    selling_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    custom_code = models.CharField(max_length=160, unique=True)
    barcode_image = models.ImageField(upload_to="barcodes/", blank=True, null=True)
    qr_image = models.ImageField(upload_to="qrcodes/", blank=True, null=True)
    received_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="received_stock_batches",
    )
    received_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["expiry_date", "batch_no"]
        indexes = [
            models.Index(fields=["product", "status"]),
            models.Index(fields=["batch_no"]),
            models.Index(fields=["custom_code"]),
            models.Index(fields=["expiry_date"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(quantity_available__gte=0),
                name="stock_batch_quantity_available_not_negative",
            ),
            models.CheckConstraint(
                condition=Q(quantity_received__gt=0),
                name="stock_batch_quantity_received_positive",
            ),
        ]

    def clean(self):
        if self.quantity_available > self.quantity_received:
            raise ValidationError("Quantity available cannot exceed quantity received.")

    def __str__(self):
        return f"{self.product} - {self.batch_no}"

    @property
    def is_expired(self):
        return self.expiry_date < timezone.localdate()


class InventoryMovement(models.Model):
    class MovementType(models.TextChoices):
        STOCK_IN = "STOCK_IN", "Stock in"
        SALE = "SALE", "Sale"
        ADJUSTMENT = "ADJUSTMENT", "Adjustment"
        RETURN = "RETURN", "Return"
        DAMAGE = "DAMAGE", "Damage"
        EXPIRED = "EXPIRED", "Expired"

    product = models.ForeignKey("catalog.Product", on_delete=models.PROTECT, related_name="inventory_movements")
    stock_batch = models.ForeignKey(StockBatch, on_delete=models.PROTECT, related_name="movements")
    movement_type = models.CharField(max_length=30, choices=MovementType.choices)
    quantity = models.PositiveIntegerField()
    reference_type = models.CharField(max_length=80, blank=True)
    reference_id = models.CharField(max_length=80, blank=True)
    note = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="inventory_movements",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["movement_type", "created_at"]),
            models.Index(fields=["reference_type", "reference_id"]),
        ]

    def __str__(self):
        return f"{self.movement_type} {self.quantity} - {self.stock_batch.batch_no}"
