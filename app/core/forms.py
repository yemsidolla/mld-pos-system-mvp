from django import forms

from .models import StoreSetting
from .permissions import ROLE_CASHIER, ROLE_INVENTORY, ROLE_MANAGER, ROLE_VIEWER

COST_VISIBILITY_CHOICES = (
    (ROLE_MANAGER, "Manager"),
    (ROLE_INVENTORY, "Inventory staff"),
    (ROLE_CASHIER, "Cashier"),
    (ROLE_VIEWER, "Viewer / Auditor"),
)


class StoreSettingForm(forms.ModelForm):
    cost_visible_roles = forms.MultipleChoiceField(
        label="Roles that can view cost & profit data",
        choices=COST_VISIBILITY_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        help_text="Owner always sees cost data. Unchecked roles get costs hidden everywhere.",
    )

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
            "cost_visible_roles",
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
