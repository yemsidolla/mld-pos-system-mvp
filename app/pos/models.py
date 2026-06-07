from decimal import Decimal

from django.conf import settings
from django.db import models


class Sale(models.Model):
    class PaymentMethod(models.TextChoices):
        CASH = "CASH", "Cash"
        ABA = "ABA", "ABA"
        KHQR = "KHQR", "KHQR"
        CARD = "CARD", "Card"
        OTHER = "OTHER", "Other"

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"
        REFUNDED = "REFUNDED", "Refunded"

    sale_no = models.CharField(max_length=30, unique=True)
    cashier = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="sales")
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    final_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    payment_method = models.CharField(max_length=20, choices=PaymentMethod.choices, default=PaymentMethod.CASH)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.COMPLETED)
    cancel_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["sale_no"]),
            models.Index(fields=["cashier", "created_at"]),
            models.Index(fields=["status", "created_at"]),
        ]

    def __str__(self):
        return self.sale_no


class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey("catalog.Product", on_delete=models.PROTECT, related_name="sale_items")
    stock_batch = models.ForeignKey("inventory.StockBatch", on_delete=models.PROTECT, related_name="sale_items")
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]
        indexes = [
            models.Index(fields=["product", "created_at"]),
            models.Index(fields=["stock_batch", "created_at"]),
        ]

    def __str__(self):
        return f"{self.sale.sale_no} - {self.product.name}"
