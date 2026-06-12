# Role-based cost visibility (configurable in Store Settings).

import core.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='storesetting',
            name='cost_visible_roles',
            field=models.JSONField(blank=True, default=core.models.default_cost_visible_roles),
        ),
    ]
