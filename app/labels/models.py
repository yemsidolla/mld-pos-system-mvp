from django.db import models


class LabelTemplate(models.Model):
    """Configurable label layout (preset fields, no drag-and-drop)."""

    FIELD_LABELS = (
        ("show_store_name", "Store"),
        ("show_logo", "Logo"),
        ("show_product_name", "Product"),
        ("show_price", "Price"),
        ("show_sku", "SKU"),
        ("show_barcode", "Barcode"),
        ("show_qr", "QR"),
        ("show_batch", "Batch"),
        ("show_expiry", "Expiry"),
        ("show_animal_type", "Animal type"),
        ("show_life_stage", "Life stage"),
    )

    class TemplateType(models.TextChoices):
        PRODUCT = "PRODUCT", "Product"
        SHELF = "SHELF", "Shelf"
        PROMOTION = "PROMOTION", "Promotion"
        CUSTOM = "CUSTOM", "Custom"

    class Orientation(models.TextChoices):
        PORTRAIT = "PORTRAIT", "Portrait"
        LANDSCAPE = "LANDSCAPE", "Landscape"

    name = models.CharField(max_length=120, unique=True)
    template_type = models.CharField(
        max_length=20, choices=TemplateType.choices, default=TemplateType.PRODUCT
    )
    paper_width_mm = models.PositiveIntegerField(default=50)
    paper_height_mm = models.PositiveIntegerField(default=30)
    orientation = models.CharField(
        max_length=20, choices=Orientation.choices, default=Orientation.PORTRAIT
    )
    font_size_px = models.PositiveIntegerField(default=11)

    show_store_name = models.BooleanField(default=True)
    show_logo = models.BooleanField(default=False)
    show_product_name = models.BooleanField(default=True)
    show_price = models.BooleanField(default=True)
    show_sku = models.BooleanField(default=False)
    show_barcode = models.BooleanField(default=True)
    show_qr = models.BooleanField(default=False)
    show_batch = models.BooleanField(default=True)
    show_expiry = models.BooleanField(default=True)
    show_animal_type = models.BooleanField(default=False)
    show_life_stage = models.BooleanField(default=False)

    header_text = models.CharField(max_length=120, blank=True)
    custom_footer = models.CharField(max_length=120, blank=True)

    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["template_type", "name"]

    def __str__(self):
        return f"{self.name} ({self.get_template_type_display()})"

    @property
    def enabled_field_labels(self):
        return [label for field, label in self.FIELD_LABELS if getattr(self, field)]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Only one default per template type.
        if self.is_default:
            LabelTemplate.objects.filter(template_type=self.template_type).exclude(pk=self.pk).update(
                is_default=False
            )

    @classmethod
    def default_for(cls, template_type):
        return (
            cls.objects.filter(template_type=template_type, is_active=True, is_default=True).first()
            or cls.objects.filter(template_type=template_type, is_active=True).first()
        )
