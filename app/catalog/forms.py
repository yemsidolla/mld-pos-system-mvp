from django import forms
from django.db.models import Q

from .models import Brand, Category, Product, Supplier


class CatalogFilterForm(forms.Form):
    q = forms.CharField(label="Search", required=False)
    status = forms.ChoiceField(
        choices=(("", "All"), ("active", "Active"), ("inactive", "Inactive")),
        required=False,
    )


class ProductFilterForm(forms.Form):
    q = forms.CharField(label="Search", required=False)
    category = forms.ModelChoiceField(queryset=Category.objects.none(), required=False)
    brand = forms.ModelChoiceField(queryset=Brand.objects.none(), required=False)
    status = forms.ChoiceField(
        choices=(("", "All"), ("active", "Active"), ("inactive", "Inactive")),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].queryset = Category.objects.filter(is_active=True).order_by("name")
        self.fields["brand"].queryset = Brand.objects.filter(is_active=True).order_by("name")


class ProductForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        category_filter = Q(is_active=True)
        brand_filter = Q(is_active=True)
        if self.instance and self.instance.pk:
            if self.instance.category_id:
                category_filter |= Q(pk=self.instance.category_id)
            if self.instance.brand_id:
                brand_filter |= Q(pk=self.instance.brand_id)
        self.fields["category"].queryset = Category.objects.filter(category_filter).order_by("name")
        self.fields["brand"].queryset = Brand.objects.filter(brand_filter).order_by("name")

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


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ("name", "description", "is_active")
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }


class BrandForm(forms.ModelForm):
    class Meta:
        model = Brand
        fields = ("name", "description", "is_active")
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }


class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ("name", "contact_person", "phone", "telegram", "address", "notes", "is_active")
        widgets = {
            "address": forms.Textarea(attrs={"rows": 3}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }


class QuickCreateNameMixin:
    def clean_name(self):
        name = self.cleaned_data["name"].strip()
        if self.Meta.model.objects.filter(name__iexact=name).exists():
            raise forms.ValidationError(f"{self.Meta.model._meta.verbose_name.title()} already exists.")
        return name


class QuickCategoryForm(QuickCreateNameMixin, forms.ModelForm):
    class Meta:
        model = Category
        fields = ("name", "description")
        widgets = {
            "description": forms.Textarea(attrs={"rows": 2}),
        }


class QuickBrandForm(QuickCreateNameMixin, forms.ModelForm):
    class Meta:
        model = Brand
        fields = ("name", "description")
        widgets = {
            "description": forms.Textarea(attrs={"rows": 2}),
        }


class QuickSupplierForm(QuickCreateNameMixin, forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ("name", "contact_person", "phone", "telegram")
