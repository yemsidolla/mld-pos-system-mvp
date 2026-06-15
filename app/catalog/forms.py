from django import forms
from django.db.models import Q

from .models import AnimalTypeOption, Brand, Category, Product, ProductTag, Supplier, SupplierProductCost


class CatalogFilterForm(forms.Form):
    q = forms.CharField(label="Search", required=False)
    status = forms.ChoiceField(
        choices=(("", "All"), ("active", "Active"), ("inactive", "Inactive")),
        required=False,
    )


class ProductFilterForm(forms.Form):
    """Column-header filters (DESIGN_SYSTEM §4.14). Every facet is multi-select,
    so values combine as OR within a column and AND across columns; ``q`` stays a
    free-text "contains" search on the Product column."""

    q = forms.CharField(label="Search", required=False)
    category = forms.ModelMultipleChoiceField(
        queryset=Category.objects.none(), required=False, widget=forms.CheckboxSelectMultiple
    )
    brand = forms.ModelMultipleChoiceField(
        queryset=Brand.objects.none(), required=False, widget=forms.CheckboxSelectMultiple
    )
    animal_type = forms.MultipleChoiceField(
        choices=Product.AnimalType.choices, required=False, widget=forms.CheckboxSelectMultiple
    )
    life_stage = forms.MultipleChoiceField(
        choices=Product.LifeStage.choices, required=False, widget=forms.CheckboxSelectMultiple
    )
    tag = forms.ModelMultipleChoiceField(
        queryset=ProductTag.objects.none(), required=False, widget=forms.CheckboxSelectMultiple
    )
    status = forms.MultipleChoiceField(
        choices=(("active", "Active"), ("inactive", "Inactive")),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].queryset = Category.objects.filter(is_active=True).order_by("name")
        self.fields["brand"].queryset = Brand.objects.filter(is_active=True).order_by("name")
        self.fields["tag"].queryset = ProductTag.objects.filter(is_active=True).order_by("name")


class ProductForm(forms.ModelForm):
    animal_types = forms.ModelMultipleChoiceField(
        queryset=AnimalTypeOption.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Animal types",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        category_filter = Q(is_active=True)
        brand_filter = Q(is_active=True)
        animal_type_filter = Q(is_active=True)
        if self.instance and self.instance.pk:
            if self.instance.category_id:
                category_filter |= Q(pk=self.instance.category_id)
            if self.instance.brand_id:
                brand_filter |= Q(pk=self.instance.brand_id)
            animal_type_filter |= Q(products=self.instance)
            if self.instance.animal_type and not self.instance.animal_types.exists():
                legacy = AnimalTypeOption.objects.filter(code=self.instance.animal_type).first()
                if legacy:
                    self.initial.setdefault("animal_types", [legacy.pk])
        self.fields["category"].queryset = Category.objects.filter(category_filter).order_by("name")
        self.fields["brand"].queryset = Brand.objects.filter(brand_filter).order_by("name")
        self.fields["animal_types"].queryset = (
            AnimalTypeOption.objects.filter(animal_type_filter).distinct().order_by("name")
        )

    def save(self, commit=True):
        product = super().save(commit=False)
        selected = list(self.cleaned_data.get("animal_types") or [])
        product.animal_type = selected[0].code if selected else ""
        if commit:
            product.save()
            self.save_m2m()
        return product

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
            "animal_types",
            "life_stage",
            "tags",
            "is_active",
        )
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "tags": forms.SelectMultiple(attrs={"size": 6}),
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


class SupplierProductCostForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        product_filter = Q(is_active=True)
        supplier_filter = Q(is_active=True)
        if self.instance and self.instance.pk:
            product_filter |= Q(pk=self.instance.product_id)
            supplier_filter |= Q(pk=self.instance.supplier_id)
        self.fields["product"].queryset = Product.objects.filter(product_filter).order_by("name")
        self.fields["supplier"].queryset = Supplier.objects.filter(supplier_filter).order_by("name")

    class Meta:
        model = SupplierProductCost
        fields = ("product", "supplier", "reference_unit_cost", "notes", "is_active")
        widgets = {
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
