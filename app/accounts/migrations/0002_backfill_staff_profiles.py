from django.conf import settings
from django.db import migrations


def backfill_profiles(apps, schema_editor):
    """Give existing users a StaffProfile based on their legacy role.

    Superusers -> Owner, Admin group -> Manager, Cashier group -> Cashier.
    Users with neither group are intentionally left without a profile so they
    keep having no dashboard access until an Owner/Manager assigns a role.
    Role strings are inlined to avoid importing app code inside a migration.
    """
    User = apps.get_model(settings.AUTH_USER_MODEL)
    StaffProfile = apps.get_model("accounts", "StaffProfile")

    for user in User.objects.all():
        if StaffProfile.objects.filter(user=user).exists():
            continue
        if user.is_superuser:
            role = "OWNER"
        elif user.groups.filter(name="Admin").exists():
            role = "MANAGER"
        elif user.groups.filter(name="Cashier").exists():
            role = "CASHIER"
        else:
            continue
        StaffProfile.objects.create(user=user, role=role)


def remove_profiles(apps, schema_editor):
    StaffProfile = apps.get_model("accounts", "StaffProfile")
    StaffProfile.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(backfill_profiles, remove_profiles),
    ]
