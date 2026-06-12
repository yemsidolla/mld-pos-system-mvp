# V8: KHR display rate and static KHQR image for the POS payment dialog.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_storesetting_quick_key_products'),
    ]

    operations = [
        migrations.AddField(
            model_name='storesetting',
            name='khr_exchange_rate',
            field=models.PositiveIntegerField(default=4100),
        ),
        migrations.AddField(
            model_name='storesetting',
            name='khqr_image',
            field=models.ImageField(blank=True, null=True, upload_to='store/'),
        ),
    ]
