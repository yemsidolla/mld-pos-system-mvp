from django.db import migrations


def create_default_promotion_template(apps, schema_editor):
    LabelTemplate = apps.get_model("labels", "LabelTemplate")
    if LabelTemplate.objects.filter(template_type="PROMOTION").exists():
        return
    LabelTemplate.objects.create(
        name="Standard Promotion Label",
        template_type="PROMOTION",
        paper_width_mm=70,
        paper_height_mm=50,
        orientation="PORTRAIT",
        font_size_px=12,
        show_store_name=True,
        show_product_name=True,
        show_price=True,
        show_barcode=False,
        show_batch=False,
        show_expiry=False,
        header_text="SPECIAL OFFER",
        is_default=True,
        is_active=True,
    )


def remove_default_promotion_template(apps, schema_editor):
    LabelTemplate = apps.get_model("labels", "LabelTemplate")
    LabelTemplate.objects.filter(name="Standard Promotion Label").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("labels", "0002_default_product_template"),
    ]

    operations = [
        migrations.RunPython(create_default_promotion_template, remove_default_promotion_template),
    ]
