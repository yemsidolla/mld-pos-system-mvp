from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandError

from accounts.models import StaffProfile
from core.permissions import (
    ADMIN_GROUP,
    CASHIER_GROUP,
    ROLE_CASHIER,
    ROLE_INVENTORY,
    ROLE_MANAGER,
    ROLE_OWNER,
    ROLE_VIEWER,
)


# CLI role name -> (StaffProfile role, legacy group, may grant Django admin)
ROLE_MAP = {
    "owner": (ROLE_OWNER, ADMIN_GROUP, True),
    "manager": (ROLE_MANAGER, ADMIN_GROUP, True),
    "admin": (ROLE_MANAGER, ADMIN_GROUP, True),  # legacy alias for manager-level access
    "inventory": (ROLE_INVENTORY, None, False),
    "cashier": (ROLE_CASHIER, CASHIER_GROUP, False),
    "viewer": (ROLE_VIEWER, None, False),
}


class Command(BaseCommand):
    help = "Assign a Melodu dashboard role to an existing user."

    def add_arguments(self, parser):
        parser.add_argument("username")
        parser.add_argument("role", choices=sorted(ROLE_MAP.keys()))
        parser.add_argument(
            "--django-admin",
            action="store_true",
            help="Also grant Django Admin (is_staff). Owner/Manager roles only.",
        )

    def handle(self, *args, **options):
        username = options["username"]
        cli_role = options["role"]
        allow_django_admin = options["django_admin"]

        role, legacy_group, can_django_admin = ROLE_MAP[cli_role]
        if allow_django_admin and not can_django_admin:
            raise CommandError(f"The '{cli_role}' role cannot be granted Django Admin access.")

        User = get_user_model()
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist as exc:
            raise CommandError(f"User '{username}' does not exist.") from exc

        admin_group, _ = Group.objects.get_or_create(name=ADMIN_GROUP)
        cashier_group, _ = Group.objects.get_or_create(name=CASHIER_GROUP)
        user.groups.remove(admin_group, cashier_group)
        if legacy_group == ADMIN_GROUP:
            user.groups.add(admin_group)
        elif legacy_group == CASHIER_GROUP:
            user.groups.add(cashier_group)

        user.is_staff = allow_django_admin
        user.is_active = True
        user.save(update_fields=["is_active", "is_staff"])

        profile, created = StaffProfile.objects.get_or_create(user=user, defaults={"role": role})
        if not created and profile.role != role:
            profile.role = role
            profile.save(update_fields=["role", "updated_at"])

        self.stdout.write(
            self.style.SUCCESS(
                f"Assigned {username} to {role}. Django Admin access: {'yes' if user.is_staff else 'no'}."
            )
        )
