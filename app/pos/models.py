from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Promotion(models.Model):
    class DiscountType(models.TextChoices):
        PERCENTAGE = "PERCENTAGE", "Percentage"
        FIXED_AMOUNT = "FIXED_AMOUNT", "Fixed amount"
        FIXED_FINAL_PRICE = "FIXED_FINAL_PRICE", "Fixed final price"

    name = models.CharField(max_length=160, unique=True)
    discount_type = models.CharField(max_length=30, choices=DiscountType.choices)
    value = models.DecimalField(max_digits=12, decimal_places=2)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)
    product = models.ForeignKey(
        "catalog.Product",
        on_delete=models.PROTECT,
        related_name="promotions",
        blank=True,
        null=True,
    )
    category = models.ForeignKey(
        "catalog.Category",
        on_delete=models.PROTECT,
        related_name="promotions",
        blank=True,
        null=True,
    )
    allow_below_cost = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_promotions",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_active", "name"]
        indexes = [
            models.Index(fields=["is_active", "start_date", "end_date"]),
            models.Index(fields=["product", "is_active"]),
            models.Index(fields=["category", "is_active"]),
        ]

    def clean(self):
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValidationError("Promotion start date cannot be after end date.")
        if not self.product_id and not self.category_id:
            raise ValidationError("Promotion must apply to a product or category.")
        if self.value < 0:
            raise ValidationError("Promotion value cannot be negative.")
        if self.discount_type == self.DiscountType.PERCENTAGE and self.value > Decimal("100.00"):
            raise ValidationError("Percentage discount cannot exceed 100%.")

    def __str__(self):
        return self.name


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
    amount_received = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    change_due = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
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
    reference_cost_at_sale = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    actual_cost_at_sale = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    landed_cost_at_sale = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    cost_basis_at_sale = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    original_unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    final_unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    promotion = models.ForeignKey(
        Promotion,
        on_delete=models.SET_NULL,
        related_name="sale_items",
        blank=True,
        null=True,
    )
    promotion_name_at_sale = models.CharField(max_length=160, blank=True)
    override_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="overridden_sale_items",
        blank=True,
        null=True,
    )
    override_reason = models.TextField(blank=True)
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
