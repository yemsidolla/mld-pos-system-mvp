from django import forms

from .models import AuthSetting, StoreSetting
from .permissions import ROLE_CASHIER, ROLE_INVENTORY, ROLE_MANAGER, ROLE_VIEWER


class AuthSettingForm(forms.ModelForm):
    class Meta:
        model = AuthSetting
        fields = ("local_login_enabled", "session_timeout_minutes")
        help_texts = {
            "local_login_enabled": (
                "Offer the local username/password form. Ignored (always on) when "
                "Authentik/OIDC is off, so the store can never lock itself out."
            ),
            "session_timeout_minutes": "How long a login lasts, in minutes. 0 = system default.",
        }


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
            "khr_exchange_rate",
            "khqr_image",
            "cost_visible_roles",
            "quick_key_products",
        )
        widgets = {
            "quick_key_products": forms.SelectMultiple(attrs={"size": 10}),
        }
        help_texts = {
            "quick_key_products": (
                "POS quick keys (Cmd/Ctrl-click to select several). "
                "Leave empty to show the last 30 days' top sellers automatically."
            ),
        }

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
