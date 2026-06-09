from django import forms

from catalog.models import Product, Supplier

from .models import StockBatch


class StockInForm(forms.Form):
    product = forms.ModelChoiceField(queryset=Product.objects.none())
    supplier = forms.ModelChoiceField(queryset=Supplier.objects.none())
    quantity = forms.IntegerField(min_value=1)
    expiry_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    actual_unit_cost = forms.DecimalField(label="Actual Unit Cost", min_value=0, max_digits=12, decimal_places=2)
    landed_unit_cost = forms.DecimalField(
        label="Landed Unit Cost",
        required=False,
        min_value=0,
        max_digits=12,
        decimal_places=2,
        help_text="Optional. Use actual cost plus shipping, import, or extra costs.",
    )
    selling_price = forms.DecimalField(min_value=0, max_digits=12, decimal_places=2)
    note = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["product"].queryset = Product.objects.filter(is_active=True).order_by("name")
        self.fields["supplier"].queryset = Supplier.objects.filter(is_active=True).order_by("name")


class LabelPrintForm(forms.Form):
    stock_batch = forms.ModelChoiceField(queryset=StockBatch.objects.none())
    label_quantity = forms.IntegerField(min_value=1, max_value=500, initial=1)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["stock_batch"].queryset = (
            StockBatch.objects.select_related("product", "supplier")
            .filter(status=StockBatch.Status.ACTIVE)
            .order_by("product__name", "expiry_date", "batch_no")
        )


class InventoryAdjustmentForm(forms.Form):
    delta_quantity = forms.IntegerField(label="Adjustment Quantity")
    reason = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}), min_length=3)

    def clean_delta_quantity(self):
        value = self.cleaned_data["delta_quantity"]
        if value == 0:
            raise forms.ValidationError("Adjustment quantity cannot be zero.")
        return value


class DamageStockForm(forms.Form):
    quantity = forms.IntegerField(min_value=1)
    reason = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}), min_length=3)


class MarkExpiredForm(forms.Form):
    reason = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}), min_length=3)
