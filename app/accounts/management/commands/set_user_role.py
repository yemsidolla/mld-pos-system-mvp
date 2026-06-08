from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandError

from core.permissions import ADMIN_GROUP, CASHIER_GROUP


class Command(BaseCommand):
    help = "Assign a Melodu role to an existing user."

    def add_arguments(self, parser):
        parser.add_argument("username")
        parser.add_argument("role", choices=["admin", "cashier"])
        parser.add_argument(
            "--django-admin",
            action="store_true",
            help="Allow the user to access Django Admin. Admin role only.",
        )

    def handle(self, *args, **options):
        username = options["username"]
        role = options["role"]
        allow_django_admin = options["django_admin"]

        if role == "cashier" and allow_django_admin:
            raise CommandError("Cashier users cannot be granted Django Admin access.")

        User = get_user_model()
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist as exc:
            raise CommandError(f"User '{username}' does not exist.") from exc

        admin_group, _ = Group.objects.get_or_create(name=ADMIN_GROUP)
        cashier_group, _ = Group.objects.get_or_create(name=CASHIER_GROUP)

        user.groups.remove(admin_group, cashier_group)
        if role == "admin":
            user.groups.add(admin_group)
            user.is_staff = allow_django_admin
        else:
            user.groups.add(cashier_group)
            user.is_staff = False

        user.is_active = True
        user.save(update_fields=["is_active", "is_staff"])

        self.stdout.write(
            self.style.SUCCESS(
                f"Assigned {username} to {role}. Django Admin access: {'yes' if user.is_staff else 'no'}."
            )
        )

