# Generated for Melodu V8 catalog refinement.

from django.db import migrations, models


ANIMAL_TYPES = [
    ("DOG", "Dog"),
    ("CAT", "Cat"),
    ("RABBIT", "Rabbit"),
    ("HAMSTER", "Hamster"),
    ("BIRD", "Bird"),
    ("FISH", "Fish"),
    ("OTHER", "Other"),
]


def seed_animal_types(apps, schema_editor):
    AnimalTypeOption = apps.get_model("catalog", "AnimalTypeOption")
    Product = apps.get_model("catalog", "Product")

    options = {}
    for code, name in ANIMAL_TYPES:
        option, _created = AnimalTypeOption.objects.get_or_create(
            code=code,
            defaults={"name": name, "is_active": True},
        )
        options[code] = option

    for product in Product.objects.exclude(animal_type=""):
        option = options.get(product.animal_type)
        if option:
            product.animal_types.add(option)


def unseed_animal_types(apps, schema_editor):
    AnimalTypeOption = apps.get_model("catalog", "AnimalTypeOption")
    AnimalTypeOption.objects.filter(code__in=[code for code, _name in ANIMAL_TYPES]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0003_producttag_product_animal_type_product_life_stage_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="AnimalTypeOption",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("code", models.CharField(max_length=20, unique=True)),
                ("name", models.CharField(max_length=80)),
                ("is_active", models.BooleanField(default=True)),
            ],
            options={
                "ordering": ["name"],
            },
        ),
        migrations.AddField(
            model_name="product",
            name="animal_types",
            field=models.ManyToManyField(blank=True, related_name="products", to="catalog.animaltypeoption"),
        ),
        migrations.RunPython(seed_animal_types, unseed_animal_types),
    ]
