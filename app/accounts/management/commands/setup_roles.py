from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand

from core.permissions import ADMIN_GROUP, CASHIER_GROUP


class Command(BaseCommand):
    help = "Create default Melodu POS roles and optionally assign a username to Admin."

    def add_arguments(self, parser):
        parser.add_argument("--admin-username", default=None)

    def handle(self, *args, **options):
        admin_group, _ = Group.objects.get_or_create(name=ADMIN_GROUP)
        Group.objects.get_or_create(name=CASHIER_GROUP)

        username = options["admin_username"]
        if username:
            user = get_user_model().objects.get(username=username)
            user.groups.add(admin_group)
            user.is_staff = True
            user.is_superuser = True
            user.save(update_fields=["is_staff", "is_superuser"])

        self.stdout.write(self.style.SUCCESS("Default roles are ready."))
