# Generated manually for Product.image_thumb (additive, nullable).

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0004_animaltypeoption_product_animal_types"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="image_thumb",
            field=models.ImageField(blank=True, null=True, upload_to="products/thumbs/"),
        ),
    ]
