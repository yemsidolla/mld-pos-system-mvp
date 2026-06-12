# V8: persist cash received and change due on the sale (shown on receipts).

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pos', '0002_promotion_saleitem_snapshots'),
    ]

    operations = [
        migrations.AddField(
            model_name='sale',
            name='amount_received',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True),
        ),
        migrations.AddField(
            model_name='sale',
            name='change_due',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True),
        ),
    ]
