from django import forms

from inventory.models import StockBatch
from pos.models import Promotion

from .models import LabelTemplate


class LabelTemplateForm(forms.ModelForm):
    class Meta:
        model = LabelTemplate
        fields = (
            "name",
            "template_type",
            "paper_width_mm",
            "paper_height_mm",
            "orientation",
            "font_size_px",
            "show_store_name",
            "show_logo",
            "show_product_name",
            "show_price",
            "show_sku",
            "show_barcode",
            "show_qr",
            "show_batch",
            "show_expiry",
            "show_animal_type",
            "show_life_stage",
            "header_text",
            "custom_footer",
            "is_default",
            "is_active",
        )

    def clean_paper_width_mm(self):
        value = self.cleaned_data["paper_width_mm"]
        if value < 10 or value > 210:
            raise forms.ValidationError("Width must be between 10mm and 210mm.")
        return value

    def clean_paper_height_mm(self):
        value = self.cleaned_data["paper_height_mm"]
        if value < 10 or value > 297:
            raise forms.ValidationError("Height must be between 10mm and 297mm.")
        return value


class LabelPrintForm(forms.Form):
    template = forms.ModelChoiceField(queryset=LabelTemplate.objects.none())
    stock_batches = forms.ModelMultipleChoiceField(queryset=StockBatch.objects.none())
    quantity = forms.IntegerField(min_value=1, max_value=200, initial=1)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["template"].queryset = LabelTemplate.objects.filter(is_active=True).order_by(
            "template_type", "name"
        )
        self.fields["stock_batches"].queryset = (
            StockBatch.objects.select_related("product")
            .filter(status=StockBatch.Status.ACTIVE)
            .order_by("product__name", "batch_no")
        )


class PromotionLabelForm(forms.Form):
    promotion = forms.ModelChoiceField(queryset=Promotion.objects.none())
    template = forms.ModelChoiceField(queryset=LabelTemplate.objects.none())
    quantity = forms.IntegerField(min_value=1, max_value=200, initial=1)
    custom_text = forms.CharField(max_length=120, required=False, initial="Special Offer")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["promotion"].queryset = Promotion.objects.filter(is_active=True).order_by("name")
        self.fields["template"].queryset = LabelTemplate.objects.filter(
            is_active=True,
            template_type__in=[LabelTemplate.TemplateType.PROMOTION, LabelTemplate.TemplateType.CUSTOM],
        ).order_by("template_type", "name")
