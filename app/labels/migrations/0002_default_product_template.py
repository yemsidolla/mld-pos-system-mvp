from django.db import migrations


def create_default_template(apps, schema_editor):
    LabelTemplate = apps.get_model("labels", "LabelTemplate")
    if LabelTemplate.objects.filter(template_type="PRODUCT").exists():
        return
    LabelTemplate.objects.create(
        name="Standard Product Label",
        template_type="PRODUCT",
        paper_width_mm=50,
        paper_height_mm=30,
        orientation="PORTRAIT",
        font_size_px=11,
        show_store_name=True,
        show_product_name=True,
        show_price=True,
        show_barcode=True,
        show_batch=True,
        show_expiry=True,
        is_default=True,
        is_active=True,
    )


def remove_default_template(apps, schema_editor):
    LabelTemplate = apps.get_model("labels", "LabelTemplate")
    LabelTemplate.objects.filter(name="Standard Product Label").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("labels", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_default_template, remove_default_template),
    ]
