from django import forms
from django.utils.translation import gettext_lazy as _

from catalog.models import Product, Supplier

from .models import StockBatch


class StockInForm(forms.Form):
    product = forms.ModelChoiceField(
        queryset=Product.objects.none(),
        help_text=_("Choose an active product with an original barcode. Use Scan Product to fill this field faster."),
    )
    supplier = forms.ModelChoiceField(
        queryset=Supplier.objects.none(),
        help_text=_("Only active suppliers are shown. Add the supplier first if it is missing."),
    )
    quantity = forms.IntegerField(
        min_value=1,
        help_text=_("Units received into this new batch. Stock-in always creates a new batch."),
    )
    expiry_date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}),
        help_text=_("Required for batch-level expiry control and label printing."),
    )
    actual_unit_cost = forms.DecimalField(
        label=_("Actual Unit Cost"),
        min_value=0,
        max_digits=12,
        decimal_places=2,
        help_text=_("Price paid to the supplier per unit for this batch."),
    )
    landed_unit_cost = forms.DecimalField(
        label=_("Landed Unit Cost"),
        required=False,
        min_value=0,
        max_digits=12,
        decimal_places=2,
        help_text=_("Optional. Use actual cost plus shipping, import, or extra costs."),
    )
    selling_price = forms.DecimalField(
        min_value=0,
        max_digits=12,
        decimal_places=2,
        help_text=_("Selling price used when this batch is selected in POS."),
    )
    note = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
        help_text=_("Optional receiving note for audit and stock traceability."),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["product"].queryset = Product.objects.filter(is_active=True).order_by("name")
        self.fields["supplier"].queryset = Supplier.objects.filter(is_active=True).order_by("name")


class LabelPrintForm(forms.Form):
    stock_batch = forms.ModelChoiceField(
        queryset=StockBatch.objects.none(),
        label=_("Stock Batch"),
        help_text=_("Choose the exact batch. Melodu custom codes resolve directly to one batch."),
    )
    label_quantity = forms.IntegerField(
        min_value=1,
        max_value=500,
        initial=1,
        help_text=_("Number of identical barcode/QR labels to preview or print."),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["stock_batch"].queryset = (
            StockBatch.objects.select_related("product", "supplier")
            .filter(status=StockBatch.Status.ACTIVE)
            .order_by("product__name", "expiry_date", "batch_no")
        )


class InventoryAdjustmentForm(forms.Form):
    delta_quantity = forms.IntegerField(label=_("Adjustment Quantity"))
    reason = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}), min_length=3)

    def clean_delta_quantity(self):
        value = self.cleaned_data["delta_quantity"]
        if value == 0:
            raise forms.ValidationError(_("Adjustment quantity cannot be zero."))
        return value


class DamageStockForm(forms.Form):
    quantity = forms.IntegerField(min_value=1)
    reason = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}), min_length=3)


class MarkExpiredForm(forms.Form):
    reason = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}), min_length=3)
