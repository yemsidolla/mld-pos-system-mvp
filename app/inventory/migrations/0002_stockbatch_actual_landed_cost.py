from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0001_initial"),
    ]

    operations = [
        migrations.RenameField(
            model_name="stockbatch",
            old_name="cost_price",
            new_name="actual_unit_cost",
        ),
        migrations.AddField(
            model_name="stockbatch",
            name="landed_unit_cost",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True),
        ),
    ]
