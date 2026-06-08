from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from audit.models import AuditLog
from audit.services import create_audit_log
from core.permissions import admin_required

from .forms import ProductFilterForm, ProductForm
from .models import Product


@admin_required
def product_list_view(request):
    form = ProductFilterForm(request.GET or None)
    products = Product.objects.select_related("category", "brand").order_by("name", "product_code")

    if form.is_valid():
        query = form.cleaned_data.get("q")
        category = form.cleaned_data.get("category")
        brand = form.cleaned_data.get("brand")
        status = form.cleaned_data.get("status")

        if query:
            products = products.filter(
                Q(name__icontains=query)
                | Q(product_code__icontains=query)
                | Q(original_barcode__icontains=query)
            )
        if category:
            products = products.filter(category=category)
        if brand:
            products = products.filter(brand=brand)
        if status == "active":
            products = products.filter(is_active=True)
        elif status == "inactive":
            products = products.filter(is_active=False)

    return render(
        request,
        "catalog/product_list.html",
        {
            "form": form,
            "products": products,
            "product_count": products.count(),
        },
    )


@admin_required
def product_create_view(request):
    form = ProductForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        product = form.save()
        create_audit_log(
            action=AuditLog.Action.CREATE,
            module="catalog",
            user=request.user,
            request=request,
            object_type="Product",
            object_id=product.pk,
            object_display=str(product),
            new_value={"product_code": product.product_code, "name": product.name},
        )
        messages.success(request, f"Product {product.product_code} was created.")
        return redirect("product-list")

    return render(request, "catalog/product_form.html", {"form": form, "mode": "create"})


@admin_required
def product_edit_view(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    old_value = {
        "product_code": product.product_code,
        "original_barcode": product.original_barcode,
        "name": product.name,
        "is_active": product.is_active,
    }
    form = ProductForm(request.POST or None, request.FILES or None, instance=product)

    if request.method == "POST" and form.is_valid():
        product = form.save()
        create_audit_log(
            action=AuditLog.Action.UPDATE,
            module="catalog",
            user=request.user,
            request=request,
            object_type="Product",
            object_id=product.pk,
            object_display=str(product),
            old_value=old_value,
            new_value={
                "product_code": product.product_code,
                "original_barcode": product.original_barcode,
                "name": product.name,
                "is_active": product.is_active,
            },
        )
        messages.success(request, f"Product {product.product_code} was updated.")
        return redirect("product-list")

    return render(request, "catalog/product_form.html", {"form": form, "mode": "edit", "product": product})
