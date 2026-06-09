import django.db.models.deletion
from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="SupplierProductCost",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "reference_unit_cost",
                    models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=12),
                ),
                ("notes", models.TextField(blank=True)),
                ("is_active", models.BooleanField(default=True)),
                (
                    "product",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="supplier_costs",
                        to="catalog.product",
                    ),
                ),
                (
                    "supplier",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="product_costs",
                        to="catalog.supplier",
                    ),
                ),
            ],
            options={
                "ordering": ["product__name", "supplier__name"],
            },
        ),
        migrations.AddConstraint(
            model_name="supplierproductcost",
            constraint=models.UniqueConstraint(
                fields=("product", "supplier"),
                name="unique_supplier_product_cost",
            ),
        ),
    ]
