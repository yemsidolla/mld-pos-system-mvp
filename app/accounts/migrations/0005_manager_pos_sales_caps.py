# Authz Phase 2: grant the two new capabilities (below-cost override, receipt
# reprint) to the built-in Manager role so behavior stays identical to when they
# were gated by the coarse is_admin_user (Owner|Manager) check. Owner holds them
# automatically via is_owner. Idempotent; leaves customized capability lists
# otherwise intact.

from django.db import migrations

NEW_MANAGER_CAPS = ["pos.override_below_cost", "sales.reprint"]


def grant(apps, schema_editor):
    Role = apps.get_model("accounts", "Role")
    try:
        manager = Role.objects.get(slug="MANAGER")
    except Role.DoesNotExist:
        return
    caps = list(manager.capabilities or [])
    changed = False
    for cap in NEW_MANAGER_CAPS:
        if cap not in caps:
            caps.append(cap)
            changed = True
    if changed:
        manager.capabilities = caps
        manager.save(update_fields=["capabilities", "updated_at"])


def revoke(apps, schema_editor):
    Role = apps.get_model("accounts", "Role")
    try:
        manager = Role.objects.get(slug="MANAGER")
    except Role.DoesNotExist:
        return
    manager.capabilities = [c for c in (manager.capabilities or []) if c not in NEW_MANAGER_CAPS]
    manager.save(update_fields=["capabilities", "updated_at"])


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_seed_builtin_roles'),
    ]

    operations = [
        migrations.RunPython(grant, revoke),
    ]
