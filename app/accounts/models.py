from django.conf import settings
from django.db import models


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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["user__username"]

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"
