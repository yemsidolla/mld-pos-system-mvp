from django import forms
from django.contrib.auth import get_user_model

from .models import Sale


class ScanForm(forms.Form):
    scan_value = forms.CharField(label="Scan Barcode or QR", max_length=180)


class AddBatchForm(forms.Form):
    stock_batch_id = forms.IntegerField(widget=forms.HiddenInput)
    quantity = forms.IntegerField(min_value=1, initial=1)


class ConfirmSaleForm(forms.Form):
    payment_method = forms.ChoiceField(choices=Sale.PaymentMethod.choices)
    discount_amount = forms.DecimalField(min_value=0, max_digits=12, decimal_places=2, initial=0)


class SaleFilterForm(forms.Form):
    date_from = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    date_to = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    cashier = forms.ModelChoiceField(required=False, queryset=get_user_model().objects.none())
    payment_method = forms.ChoiceField(required=False, choices=[("", "All")] + list(Sale.PaymentMethod.choices))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["cashier"].queryset = get_user_model().objects.filter(sales__isnull=False).distinct().order_by("username")


class CancelSaleForm(forms.Form):
    reason = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}), min_length=3)
