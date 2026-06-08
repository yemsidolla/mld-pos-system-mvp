from django import forms

from .models import Brand, Category, Product


class ProductFilterForm(forms.Form):
    q = forms.CharField(label="Search", required=False)
    category = forms.ModelChoiceField(queryset=Category.objects.filter(is_active=True), required=False)
    brand = forms.ModelChoiceField(queryset=Brand.objects.filter(is_active=True), required=False)
    status = forms.ChoiceField(
        choices=(("", "All"), ("active", "Active"), ("inactive", "Inactive")),
        required=False,
    )


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = (
            "product_code",
            "original_barcode",
            "name",
            "category",
            "brand",
            "unit",
            "default_cost_price",
            "default_selling_price",
            "min_stock",
            "description",
            "image",
            "is_active",
        )
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }

