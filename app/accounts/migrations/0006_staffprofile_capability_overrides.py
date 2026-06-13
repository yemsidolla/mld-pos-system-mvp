# Authz Phase 4: per-user capability overrides.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_manager_pos_sales_caps'),
    ]

    operations = [
        migrations.AddField(
            model_name='staffprofile',
            name='extra_capabilities',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name='staffprofile',
            name='revoked_capabilities',
            field=models.JSONField(blank=True, default=list),
        ),
    ]
