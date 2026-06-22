from django import forms
from django.utils.translation import gettext_lazy as _

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
        help_texts = {
            "paper_width_mm": _("Physical label width in millimeters."),
            "paper_height_mm": _("Physical label height in millimeters."),
            "orientation": _("Choose landscape when the label stock is wider than it is tall."),
            "font_size_px": _("Base print font size. Test with the physical printer before making it default."),
            "show_barcode": _("Code128 barcode generated from the Melodu custom batch code."),
            "show_qr": _("QR code generated from the same Melodu custom batch code."),
            "is_default": _("Only one active default is kept per template type."),
            "is_active": _("Inactive templates stay saved but cannot be selected for printing."),
        }

    def clean_paper_width_mm(self):
        value = self.cleaned_data["paper_width_mm"]
        if value < 10 or value > 210:
            raise forms.ValidationError(_("Width must be between 10mm and 210mm."))
        return value

    def clean_paper_height_mm(self):
        value = self.cleaned_data["paper_height_mm"]
        if value < 10 or value > 297:
            raise forms.ValidationError(_("Height must be between 10mm and 297mm."))
        return value


class LabelPrintForm(forms.Form):
    template = forms.ModelChoiceField(
        queryset=LabelTemplate.objects.none(),
        help_text=_("Choose the layout used for every selected batch."),
    )
    stock_batches = forms.ModelMultipleChoiceField(
        queryset=StockBatch.objects.none(),
        help_text=_("Select one or more active batches. Use Scan Batch to fill one batch quickly."),
    )
    quantity = forms.IntegerField(
        min_value=1,
        max_value=200,
        initial=1,
        help_text=_("Copies per selected batch."),
    )

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
    promotion = forms.ModelChoiceField(
        queryset=Promotion.objects.none(),
        help_text=_("Only active promotions are listed."),
    )
    template = forms.ModelChoiceField(
        queryset=LabelTemplate.objects.none(),
        help_text=_("Promotion or custom templates can be used for offer labels."),
    )
    quantity = forms.IntegerField(
        min_value=1,
        max_value=200,
        initial=1,
        help_text=_("Copies per active product in the promotion."),
    )
    custom_text = forms.CharField(
        max_length=120,
        required=False,
        initial=_("Special Offer"),
        help_text=_("Optional offer text printed on every promotion label."),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["promotion"].queryset = Promotion.objects.filter(is_active=True).order_by("name")
        self.fields["template"].queryset = LabelTemplate.objects.filter(
            is_active=True,
            template_type__in=[LabelTemplate.TemplateType.PROMOTION, LabelTemplate.TemplateType.CUSTOM],
        ).order_by("template_type", "name")
