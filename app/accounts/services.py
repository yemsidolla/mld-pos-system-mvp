from django.contrib.auth.models import Group

from core.permissions import ADMIN_GROUP, CASHIER_GROUP, ROLE_CASHIER, ROLE_MANAGER, ROLE_OWNER

from .models import StaffProfile


def set_role(user, role):
    """Assign ``role`` via StaffProfile; ``None`` clears the assignment."""
    if role is None:
        StaffProfile.objects.filter(user=user).delete()
        return None
    profile, created = StaffProfile.objects.get_or_create(user=user, defaults={"role": role})
    if not created and profile.role != role:
        profile.role = role
        profile.save(update_fields=["role", "updated_at"])
    return profile


def sync_legacy_group(user, role):
    """Keep the legacy Admin/Cashier groups aligned with the role (map and keep)."""
    admin_group, _ = Group.objects.get_or_create(name=ADMIN_GROUP)
    cashier_group, _ = Group.objects.get_or_create(name=CASHIER_GROUP)
    user.groups.remove(admin_group, cashier_group)
    if role in (ROLE_OWNER, ROLE_MANAGER):
        user.groups.add(admin_group)
    elif role == ROLE_CASHIER:
        user.groups.add(cashier_group)
