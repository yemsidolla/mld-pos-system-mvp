from decimal import Decimal

from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Category(TimeStampedModel):
    name = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class Brand(TimeStampedModel):
    name = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Supplier(TimeStampedModel):
    name = models.CharField(max_length=160, unique=True)
    contact_person = models.CharField(max_length=120, blank=True)
    phone = models.CharField(max_length=40, blank=True)
    telegram = models.CharField(max_length=80, blank=True)
    address = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class SupplierProductCost(TimeStampedModel):
    product = models.ForeignKey("Product", on_delete=models.CASCADE, related_name="supplier_costs")
    supplier = models.ForeignKey("Supplier", on_delete=models.CASCADE, related_name="product_costs")
    reference_unit_cost = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["product__name", "supplier__name"]
        constraints = [
            models.UniqueConstraint(fields=["product", "supplier"], name="unique_supplier_product_cost"),
        ]

    def __str__(self):
        return f"{self.product} - {self.supplier}"


class ProductTag(TimeStampedModel):
    """Flexible classification label (e.g. Grain Free, Dental Care, Small Breed)."""

    name = models.CharField(max_length=80, unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Product(TimeStampedModel):
    class AnimalType(models.TextChoices):
        DOG = "DOG", "Dog"
        CAT = "CAT", "Cat"
        RABBIT = "RABBIT", "Rabbit"
        HAMSTER = "HAMSTER", "Hamster"
        BIRD = "BIRD", "Bird"
        FISH = "FISH", "Fish"
        OTHER = "OTHER", "Other"

    class LifeStage(models.TextChoices):
        BABY = "BABY", "Baby"
        PUPPY = "PUPPY", "Puppy"
        KITTEN = "KITTEN", "Kitten"
        ADULT = "ADULT", "Adult"
        SENIOR = "SENIOR", "Senior"
        ALL = "ALL", "All ages"

    product_code = models.CharField(max_length=40, unique=True)
    original_barcode = models.CharField(
        max_length=80,
        unique=True,
        blank=True,
        null=True,
        help_text="Manufacturer barcode. Leave blank only when the product has no barcode.",
    )
    name = models.CharField(max_length=180)
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="products",
        null=True,
        blank=True,
    )
    brand = models.ForeignKey(
        Brand,
        on_delete=models.PROTECT,
        related_name="products",
        null=True,
        blank=True,
    )
    unit = models.CharField(max_length=40, default="Unit")
    default_cost_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    default_selling_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    min_stock = models.PositiveIntegerField(default=0)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="products/", blank=True, null=True)
    animal_type = models.CharField(max_length=20, choices=AnimalType.choices, blank=True)
    life_stage = models.CharField(max_length=20, choices=LifeStage.choices, blank=True)
    tags = models.ManyToManyField(ProductTag, blank=True, related_name="products")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name", "product_code"]

    def __str__(self):
        return f"{self.name} ({self.product_code})"
