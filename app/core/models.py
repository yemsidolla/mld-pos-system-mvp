from django.db import models


def default_cost_visible_roles():
    # Matches pre-V6 behavior: every role that could already reach a
    # cost-bearing page keeps seeing costs until an Owner narrows the list.
    return ["MANAGER", "INVENTORY", "VIEWER"]


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
    # Roles (besides Owner, who always sees costs) allowed to view cost and
    # profit data. List of StaffProfile.Role values, e.g. ["MANAGER"].
    cost_visible_roles = models.JSONField(default=default_cost_visible_roles, blank=True)
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
