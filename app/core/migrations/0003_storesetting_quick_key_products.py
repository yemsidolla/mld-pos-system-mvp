# POS quick keys (V8): hand-picked products shown as tap buttons.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0001_initial'),
        ('core', '0002_storesetting_cost_visible_roles'),
    ]

    operations = [
        migrations.AddField(
            model_name='storesetting',
            name='quick_key_products',
            field=models.ManyToManyField(blank=True, limit_choices_to={'is_active': True}, related_name='+', to='catalog.product'),
        ),
    ]
