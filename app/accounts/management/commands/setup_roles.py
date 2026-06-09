from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand

from core.permissions import ADMIN_GROUP, CASHIER_GROUP


class Command(BaseCommand):
    help = "Create default Melodu POS roles and optionally assign a username to Admin."

    def add_arguments(self, parser):
        parser.add_argument("--admin-username", default=None)
        parser.add_argument("--password", default=None, help="Create or update the admin user's password.")
        parser.add_argument("--email", default="", help="Email address to use when creating the admin user.")

    def handle(self, *args, **options):
        admin_group, _ = Group.objects.get_or_create(name=ADMIN_GROUP)
        Group.objects.get_or_create(name=CASHIER_GROUP)

        username = options["admin_username"]
        if username:
            password = options["password"]
            defaults = {
                "email": options["email"],
                "is_staff": True,
                "is_superuser": True,
            }
            if password:
                user, _created = get_user_model().objects.get_or_create(username=username, defaults=defaults)
                user.set_password(password)
            else:
                user = get_user_model().objects.get(username=username)
            user.groups.add(admin_group)
            user.is_staff = True
            user.is_superuser = True
            update_fields = ["is_staff", "is_superuser"]
            if password:
                update_fields.append("password")
            if options["email"] and user.email != options["email"]:
                user.email = options["email"]
                update_fields.append("email")
            user.save(update_fields=update_fields)

        self.stdout.write(self.style.SUCCESS("Default roles are ready."))
