from django.db import models


class StoreSetting(models.Model):
    """Singleton store identity and receipt/printer configuration.

    Always stored as a single row (pk=1). Use ``StoreSetting.load()`` to read or
    create the row with defaults.
    """

    store_name = models.CharField(max_length=160, default="Melodu Pet Store")
    address = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=40, blank=True)
    logo = models.ImageField(upload_to="store/", blank=True, null=True)
    receipt_header = models.CharField(max_length=255, blank=True)
    receipt_footer = models.CharField(max_length=255, blank=True, default="Thank you!")
    receipt_paper_width_mm = models.PositiveIntegerField(default=80)
    receipt_font_size_px = models.PositiveIntegerField(default=12)
    show_logo_on_receipt = models.BooleanField(default=False)
    currency_symbol = models.CharField(max_length=8, default="$")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Store setting"
        verbose_name_plural = "Store settings"

    def __str__(self):
        return self.store_name

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _created = cls.objects.get_or_create(pk=1)
        return obj
