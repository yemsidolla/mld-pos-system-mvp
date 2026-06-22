from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from catalog.models import Category, Product

from .models import Promotion, Sale


class ScanForm(forms.Form):
    scan_value = forms.CharField(label=_("Scan Barcode or QR"), max_length=180)


class AddBatchForm(forms.Form):
    stock_batch_id = forms.IntegerField(widget=forms.HiddenInput)
    quantity = forms.IntegerField(min_value=1, initial=1)


class ConfirmSaleForm(forms.Form):
    payment_method = forms.ChoiceField(choices=Sale.PaymentMethod.choices)
    discount_amount = forms.DecimalField(min_value=0, max_digits=12, decimal_places=2, initial=0)
    amount_received = forms.DecimalField(required=False, min_value=0, max_digits=12, decimal_places=2)
    override_reason = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 2}),
        help_text=_("Required only for admin below-cost override."),
    )


class SaleFilterForm(forms.Form):
    date_from = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    date_to = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    cashier = forms.ModelChoiceField(required=False, queryset=get_user_model().objects.none())
    payment_method = forms.ChoiceField(required=False, choices=[("", _("All"))] + list(Sale.PaymentMethod.choices))
    status = forms.ChoiceField(required=False, choices=[("", _("All"))] + list(Sale.Status.choices))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["cashier"].queryset = get_user_model().objects.filter(sales__isnull=False).distinct().order_by("username")


class CancelSaleForm(forms.Form):
    reason = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}), min_length=3)


class PromotionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.created_by = kwargs.pop("created_by", None)
        super().__init__(*args, **kwargs)
        self.fields["product"].queryset = Product.objects.filter(is_active=True).order_by("name")
        self.fields["category"].queryset = Category.objects.filter(is_active=True).order_by("name")
        self.fields["discount_type"].help_text = _("Percentage, fixed amount off, or fixed final price.")
        self.fields["value"].help_text = _("Use the amount for the selected discount type. Percent values cannot exceed 100.")
        self.fields["product"].help_text = _("Use for an exact product promotion.")
        self.fields["category"].help_text = _("Use for all active products in one category.")
        self.fields["allow_below_cost"].help_text = _("Only allow this when the owner accepts selling below cost.")

    def clean(self):
        cleaned_data = super().clean()
        product = cleaned_data.get("product")
        category = cleaned_data.get("category")
        if product and category:
            raise forms.ValidationError(_("Choose either a product or a category, not both."))
        return cleaned_data

    class Meta:
        model = Promotion
        fields = (
            "name",
            "discount_type",
            "value",
            "start_date",
            "end_date",
            "is_active",
            "product",
            "category",
            "allow_below_cost",
        )
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
        }

    def save(self, commit=True):
        promotion = super().save(commit=False)
        if promotion.pk is None and self.created_by is not None:
            promotion.created_by = self.created_by
        if commit:
            promotion.full_clean()
            promotion.save()
            self.save_m2m()
        return promotion
