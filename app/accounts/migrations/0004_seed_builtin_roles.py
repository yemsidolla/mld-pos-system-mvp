# Authz Phase 1: seed the five built-in roles to reproduce the original
# hardcoded permission matrix exactly. Capability lists are inlined (frozen
# history); the canonical source going forward is core.capabilities.BUILTIN_ROLES.

from django.db import migrations

BUILTIN_ROLES = [
    ("OWNER", "Owner", 10, True, []),
    (
        "MANAGER",
        "Manager",
        20,
        False,
        [
            "pos.access",
            "sales.view_history",
            "sales.cancel",
            "catalog.manage",
            "promotions.manage",
            "inventory.manage",
            "reports.view",
            "system.manage_users",
            "system.manage_settings",
            "system.view_audit",
            "system.view_logs",
        ],
    ),
    ("INVENTORY", "Inventory staff", 30, False, ["inventory.manage"]),
    ("CASHIER", "Cashier", 40, False, ["pos.access"]),
    ("VIEWER", "Viewer / Auditor", 50, False, ["sales.view_history", "reports.view"]),
]


def seed(apps, schema_editor):
    Role = apps.get_model("accounts", "Role")
    for slug, name, rank, is_owner, capabilities in BUILTIN_ROLES:
        Role.objects.update_or_create(
            slug=slug,
            defaults={
                "name": name,
                "rank": rank,
                "is_owner": is_owner,
                "is_builtin": True,
                "capabilities": capabilities,
            },
        )


def unseed(apps, schema_editor):
    Role = apps.get_model("accounts", "Role")
    Role.objects.filter(is_builtin=True).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_role'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
