from django.conf import settings
from django.db import models


class Role(models.Model):
    """A named set of capabilities (Authz Phase 1).

    The five built-in roles are seeded to reproduce the original hardcoded
    matrix; custom roles can be added later. ``slug`` matches the value stored
    in ``StaffProfile.role`` and the ``ROLE_*`` constants in ``core.permissions``.
    Capabilities are stored as a list of capability keys
    (see ``core.capabilities``); an ``is_owner`` role implicitly holds all of
    them and can never be locked out.
    """

    slug = models.CharField(max_length=40, unique=True)
    name = models.CharField(max_length=80)
    is_builtin = models.BooleanField(default=False)
    is_owner = models.BooleanField(default=False)
    capabilities = models.JSONField(default=list, blank=True)
    rank = models.PositiveIntegerField(default=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["rank", "name"]

    def __str__(self):
        return self.name


class StaffProfile(models.Model):
    """V4 role assignment for a dashboard user.

    Role values intentionally mirror the ``ROLE_*`` constants in
    ``core.permissions``. Keep the two in sync; permission checks read
    ``staff_profile.role`` as a plain string to avoid an import cycle.
    """

    class Role(models.TextChoices):
        OWNER = "OWNER", "Owner"
        MANAGER = "MANAGER", "Manager"
        INVENTORY = "INVENTORY", "Inventory staff"
        CASHIER = "CASHIER", "Cashier"
        VIEWER = "VIEWER", "Viewer / Auditor"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="staff_profile",
    )
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CASHIER)
    # Per-user capability overrides (Authz Phase 4): granted beyond the role, or
    # blocked even when the role grants them. Effective = role caps ∪ extra − revoked.
    extra_capabilities = models.JSONField(default=list, blank=True)
    revoked_capabilities = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["user__username"]

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"
