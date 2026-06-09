from django import forms

from .models import StoreSetting


class StoreSettingForm(forms.ModelForm):
    class Meta:
        model = StoreSetting
        fields = (
            "store_name",
            "address",
            "phone",
            "logo",
            "receipt_header",
            "receipt_footer",
            "receipt_paper_width_mm",
            "receipt_font_size_px",
            "show_logo_on_receipt",
            "currency_symbol",
        )

    def clean_receipt_paper_width_mm(self):
        width = self.cleaned_data["receipt_paper_width_mm"]
        if width < 40 or width > 120:
            raise forms.ValidationError("Receipt width must be between 40mm and 120mm.")
        return width

    def clean_receipt_font_size_px(self):
        size = self.cleaned_data["receipt_font_size_px"]
        if size < 8 or size > 24:
            raise forms.ValidationError("Font size must be between 8px and 24px.")
        return size
