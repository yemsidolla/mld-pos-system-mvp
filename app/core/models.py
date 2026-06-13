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
    # USD -> KHR display rate for the POS and receipts (e.g. 4100).
    khr_exchange_rate = models.PositiveIntegerField(default=4100)
    # Static KHQR/Bakong code shown in the POS payment dialog.
    khqr_image = models.ImageField(upload_to="store/", blank=True, null=True)
    # Roles (besides Owner, who always sees costs) allowed to view cost and
    # profit data. List of StaffProfile.Role values, e.g. ["MANAGER"].
    cost_visible_roles = models.JSONField(default=default_cost_visible_roles, blank=True)
    # Hand-picked POS quick keys; when empty the POS falls back to the
    # best-selling products of the last 30 days.
    quick_key_products = models.ManyToManyField(
        "catalog.Product",
        blank=True,
        related_name="+",
        limit_choices_to={"is_active": True},
    )
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


class AuthSetting(models.Model):
    """Singleton login/authentication settings editable by an Owner (Authz Phase 5).

    The authentication *mode* (local vs Authentik/OIDC) stays env-driven because
    it wires up apps and backends at startup; only the safe runtime toggles live
    here.
    """

    # Whether the local username/password form is offered. Honoured only when
    # OIDC is enabled — with no OIDC alternative the login view forces it on so
    # the store can never lock itself out.
    local_login_enabled = models.BooleanField(default=True)
    # Session lifetime in minutes; 0 means use the Django default.
    session_timeout_minutes = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Authentication setting"
        verbose_name_plural = "Authentication settings"

    def __str__(self):
        return "Authentication settings"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _created = cls.objects.get_or_create(pk=1)
        return obj
