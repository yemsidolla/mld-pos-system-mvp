import django.db.models.deletion
from decimal import Decimal
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0001_initial"),
        ("inventory", "0002_stockbatch_actual_landed_cost"),
        ("pos", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Promotion",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=160, unique=True)),
                (
                    "discount_type",
                    models.CharField(
                        choices=[
                            ("PERCENTAGE", "Percentage"),
                            ("FIXED_AMOUNT", "Fixed amount"),
                            ("FIXED_FINAL_PRICE", "Fixed final price"),
                        ],
                        max_length=30,
                    ),
                ),
                ("value", models.DecimalField(decimal_places=2, max_digits=12)),
                ("start_date", models.DateField()),
                ("end_date", models.DateField()),
                ("is_active", models.BooleanField(default=True)),
                ("allow_below_cost", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "category",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="promotions",
                        to="catalog.category",
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="created_promotions",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "product",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="promotions",
                        to="catalog.product",
                    ),
                ),
            ],
            options={
                "ordering": ["-is_active", "name"],
            },
        ),
        migrations.AddField(
            model_name="saleitem",
            name="actual_cost_at_sale",
            field=models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=12),
        ),
        migrations.AddField(
            model_name="saleitem",
            name="cost_basis_at_sale",
            field=models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=12),
        ),
        migrations.AddField(
            model_name="saleitem",
            name="discount_amount",
            field=models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=12),
        ),
        migrations.AddField(
            model_name="saleitem",
            name="final_unit_price",
            field=models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=12),
        ),
        migrations.AddField(
            model_name="saleitem",
            name="landed_cost_at_sale",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True),
        ),
        migrations.AddField(
            model_name="saleitem",
            name="original_unit_price",
            field=models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=12),
        ),
        migrations.AddField(
            model_name="saleitem",
            name="override_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="overridden_sale_items",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="saleitem",
            name="override_reason",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="saleitem",
            name="promotion",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="sale_items",
                to="pos.promotion",
            ),
        ),
        migrations.AddField(
            model_name="saleitem",
            name="promotion_name_at_sale",
            field=models.CharField(blank=True, max_length=160),
        ),
        migrations.AddField(
            model_name="saleitem",
            name="reference_cost_at_sale",
            field=models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=12),
        ),
        migrations.AddIndex(
            model_name="promotion",
            index=models.Index(fields=["is_active", "start_date", "end_date"], name="pos_promoti_is_acti_1c82ed_idx"),
        ),
        migrations.AddIndex(
            model_name="promotion",
            index=models.Index(fields=["product", "is_active"], name="pos_promoti_product_e780b8_idx"),
        ),
        migrations.AddIndex(
            model_name="promotion",
            index=models.Index(fields=["category", "is_active"], name="pos_promoti_categor_ae2797_idx"),
        ),
    ]
