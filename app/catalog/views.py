from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from audit.models import AuditLog
from audit.services import create_audit_log
from core.pagination import paginate
from core.permissions import admin_required, can_manage_catalog, costs_required

from .forms import (
    BrandForm,
    CatalogFilterForm,
    CategoryForm,
    ProductFilterForm,
    ProductForm,
    QuickBrandForm,
    QuickCategoryForm,
    QuickSupplierForm,
    SupplierForm,
    SupplierProductCostForm,
)
from .models import Brand, Category, Product, Supplier, SupplierProductCost


QUICK_CREATE_FORMS = {
    "category": (QuickCategoryForm, "Category"),
    "brand": (QuickBrandForm, "Brand"),
    "supplier": (QuickSupplierForm, "Supplier"),
}


def _apply_status_filter(queryset, status):
    if status == "active":
        return queryset.filter(is_active=True)
    if status == "inactive":
        return queryset.filter(is_active=False)
    return queryset


def _apply_search_filter(queryset, query, fields):
    if not query:
        return queryset
    condition = Q()
    for field in fields:
        condition |= Q(**{f"{field}__icontains": query})
    return queryset.filter(condition)


def _model_snapshot(obj, fields):
    if obj is None:
        return None
    snapshot = {}
    for field in fields:
        try:
            field_obj = obj._meta.get_field(field)
        except Exception:  # pragma: no cover - defensive
            field_obj = None
        if field_obj is not None and field_obj.many_to_many:
            snapshot[field] = sorted(str(item) for item in getattr(obj, field).all()) if obj.pk else []
            continue
        value = getattr(obj, field)
        snapshot[field] = str(value) if value is not None else None
    return snapshot


def _form_errors_payload(form):
    return {field: [str(error) for error in errors] for field, errors in form.errors.items()}


@require_POST
@login_required
def catalog_quick_create_view(request):
    if not can_manage_catalog(request.user):
        return JsonResponse({"status": "error", "error": "Access denied."}, status=403)

    item_type = request.POST.get("type", "").strip().lower()
    config = QUICK_CREATE_FORMS.get(item_type)
    if config is None:
        return JsonResponse({"status": "error", "error": "Unsupported quick-create type."}, status=400)

    form_class, object_type = config
    form = form_class(request.POST)
    if not form.is_valid():
        return JsonResponse({"status": "error", "errors": _form_errors_payload(form)}, status=400)

    with transaction.atomic():
        obj = form.save(commit=False)
        obj.is_active = True
        obj.save()
        create_audit_log(
            action=AuditLog.Action.CREATE,
            module="catalog",
            user=request.user,
            request=request,
            object_type=object_type,
            object_id=obj.pk,
            object_display=str(obj),
            new_value=_model_snapshot(obj, form_class.Meta.fields + ("is_active",)),
        )

    return JsonResponse(
        {
            "status": "ok",
            "item": {
                "id": obj.pk,
                "label": obj.name,
                "type": item_type,
            },
        }
    )


def _master_data_list_view(
    request,
    *,
    title,
    subtitle,
    queryset,
    search_fields,
    columns,
    row_builder,
    create_url_name,
    create_label,
    empty_message,
):
    form = CatalogFilterForm(request.GET or None)
    objects = queryset

    if form.is_valid():
        objects = _apply_search_filter(objects, form.cleaned_data.get("q"), search_fields)
        objects = _apply_status_filter(objects, form.cleaned_data.get("status"))

    rows = [
        {
            "object": obj,
            "cells": row_builder(obj),
            "edit_url": reverse(columns["edit_url_name"], kwargs={columns["edit_kwarg"]: obj.pk}),
        }
        for obj in objects
    ]

    return render(
        request,
        "catalog/master_data_list.html",
        {
            "form": form,
            "title": title,
            "subtitle": subtitle,
            "rows": rows,
            "columns": columns["labels"],
            "create_url": reverse(create_url_name),
            "create_label": create_label,
            "empty_message": empty_message,
            "item_count": len(rows),
        },
    )


def _master_data_form_view(
    request,
    *,
    form_class,
    instance,
    mode,
    title,
    subtitle,
    list_url_name,
    object_type,
):
    field_names = form_class.Meta.fields
    old_value = _model_snapshot(instance, field_names)
    form = form_class(request.POST or None, instance=instance)

    if request.method == "POST" and form.is_valid():
        obj = form.save()
        create_audit_log(
            action=AuditLog.Action.CREATE if mode == "create" else AuditLog.Action.UPDATE,
            module="catalog",
            user=request.user,
            request=request,
            object_type=object_type,
            object_id=obj.pk,
            object_display=str(obj),
            old_value=old_value,
            new_value=_model_snapshot(obj, field_names),
        )
        messages.success(request, f"{object_type} {obj.name} was {'created' if mode == 'create' else 'updated'}.")
        return redirect(list_url_name)

    return render(
        request,
        "catalog/master_data_form.html",
        {
            "form": form,
            "mode": mode,
            "title": title,
            "subtitle": subtitle,
            "back_url": reverse(list_url_name),
            "object": instance,
        },
    )


@admin_required
def product_list_view(request):
    form = ProductFilterForm(request.GET or None)
    products = (
        Product.objects.select_related("category", "brand")
        .prefetch_related("tags")
        .order_by("name", "product_code")
    )

    if form.is_valid():
        query = form.cleaned_data.get("q")
        category = form.cleaned_data.get("category")
        brand = form.cleaned_data.get("brand")
        animal_type = form.cleaned_data.get("animal_type")
        life_stage = form.cleaned_data.get("life_stage")
        tag = form.cleaned_data.get("tag")
        status = form.cleaned_data.get("status")

        if query:
            products = products.filter(
                Q(name__icontains=query)
                | Q(product_code__icontains=query)
                | Q(original_barcode__icontains=query)
                | Q(tags__name__icontains=query)
            ).distinct()
        if category:
            products = products.filter(category=category)
        if brand:
            products = products.filter(brand=brand)
        if animal_type:
            products = products.filter(animal_type=animal_type)
        if life_stage:
            products = products.filter(life_stage=life_stage)
        if tag:
            products = products.filter(tags=tag)
        products = _apply_status_filter(products, status)

    product_count = products.count()
    page_obj, querystring = paginate(request, products)

    return render(
        request,
        "catalog/product_list.html",
        {
            "form": form,
            "products": page_obj,
            "page_obj": page_obj,
            "querystring": querystring,
            "product_count": product_count,
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
            new_value=_model_snapshot(product, ProductForm.Meta.fields),
        )
        create_audit_log(
            action=AuditLog.Action.COST_CHANGE,
            module="catalog",
            user=request.user,
            request=request,
            object_type="Product",
            object_id=product.pk,
            object_display=str(product),
            new_value={"default_cost_price": str(product.default_cost_price)},
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
        "default_cost_price": str(product.default_cost_price),
        "default_selling_price": str(product.default_selling_price),
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
                "default_cost_price": str(product.default_cost_price),
                "default_selling_price": str(product.default_selling_price),
                "is_active": product.is_active,
            },
        )
        if old_value["default_cost_price"] != str(product.default_cost_price):
            create_audit_log(
                action=AuditLog.Action.COST_CHANGE,
                module="catalog",
                user=request.user,
                request=request,
                object_type="Product",
                object_id=product.pk,
                object_display=str(product),
                old_value={"default_cost_price": old_value["default_cost_price"]},
                new_value={"default_cost_price": str(product.default_cost_price)},
            )
        messages.success(request, f"Product {product.product_code} was updated.")
        return redirect("product-list")

    return render(request, "catalog/product_form.html", {"form": form, "mode": "edit", "product": product})


@admin_required
def category_list_view(request):
    return _master_data_list_view(
        request,
        title="Categories",
        subtitle="Maintain the product groups used for catalog filtering and reporting.",
        queryset=Category.objects.annotate(product_count=Count("products")).order_by("name"),
        search_fields=("name", "description"),
        columns={
            "labels": ["Description", "Products"],
            "edit_url_name": "category-edit",
            "edit_kwarg": "category_id",
        },
        row_builder=lambda category: [category.description or "-", category.product_count],
        create_url_name="category-create",
        create_label="New Category",
        empty_message="No categories found.",
    )


@admin_required
def category_create_view(request):
    return _master_data_form_view(
        request,
        form_class=CategoryForm,
        instance=None,
        mode="create",
        title="New Category",
        subtitle="Create a category before assigning it to products.",
        list_url_name="category-list",
        object_type="Category",
    )


@admin_required
def category_edit_view(request, category_id):
    category = get_object_or_404(Category, pk=category_id)
    return _master_data_form_view(
        request,
        form_class=CategoryForm,
        instance=category,
        mode="edit",
        title="Edit Category",
        subtitle="Update category naming, description, or active status.",
        list_url_name="category-list",
        object_type="Category",
    )


@admin_required
def brand_list_view(request):
    return _master_data_list_view(
        request,
        title="Brands",
        subtitle="Maintain brand names used on products and catalog filters.",
        queryset=Brand.objects.annotate(product_count=Count("products")).order_by("name"),
        search_fields=("name", "description"),
        columns={
            "labels": ["Description", "Products"],
            "edit_url_name": "brand-edit",
            "edit_kwarg": "brand_id",
        },
        row_builder=lambda brand: [brand.description or "-", brand.product_count],
        create_url_name="brand-create",
        create_label="New Brand",
        empty_message="No brands found.",
    )


@admin_required
def brand_create_view(request):
    return _master_data_form_view(
        request,
        form_class=BrandForm,
        instance=None,
        mode="create",
        title="New Brand",
        subtitle="Create a brand before assigning it to products.",
        list_url_name="brand-list",
        object_type="Brand",
    )


@admin_required
def brand_edit_view(request, brand_id):
    brand = get_object_or_404(Brand, pk=brand_id)
    return _master_data_form_view(
        request,
        form_class=BrandForm,
        instance=brand,
        mode="edit",
        title="Edit Brand",
        subtitle="Update brand naming, description, or active status.",
        list_url_name="brand-list",
        object_type="Brand",
    )


@admin_required
def supplier_list_view(request):
    return _master_data_list_view(
        request,
        title="Suppliers",
        subtitle="Maintain supplier contacts used when receiving stock.",
        queryset=Supplier.objects.annotate(batch_count=Count("stock_batches")).order_by("name"),
        search_fields=("name", "contact_person", "phone", "telegram", "address", "notes"),
        columns={
            "labels": ["Contact", "Phone", "Telegram", "Batches"],
            "edit_url_name": "supplier-edit",
            "edit_kwarg": "supplier_id",
        },
        row_builder=lambda supplier: [
            supplier.contact_person or "-",
            supplier.phone or "-",
            supplier.telegram or "-",
            supplier.batch_count,
        ],
        create_url_name="supplier-create",
        create_label="New Supplier",
        empty_message="No suppliers found.",
    )


@admin_required
def supplier_create_view(request):
    return _master_data_form_view(
        request,
        form_class=SupplierForm,
        instance=None,
        mode="create",
        title="New Supplier",
        subtitle="Create a supplier before using it in stock-in.",
        list_url_name="supplier-list",
        object_type="Supplier",
    )


@admin_required
def supplier_edit_view(request, supplier_id):
    supplier = get_object_or_404(Supplier, pk=supplier_id)
    return _master_data_form_view(
        request,
        form_class=SupplierForm,
        instance=supplier,
        mode="edit",
        title="Edit Supplier",
        subtitle="Update supplier contact details or active status.",
        list_url_name="supplier-list",
        object_type="Supplier",
    )


@admin_required
@costs_required
def supplier_product_cost_list_view(request):
    query = request.GET.get("q", "").strip()
    costs = SupplierProductCost.objects.select_related("product", "supplier").order_by("product__name", "supplier__name")
    if query:
        costs = costs.filter(
            Q(product__name__icontains=query)
            | Q(product__product_code__icontains=query)
            | Q(supplier__name__icontains=query)
        )
    return render(
        request,
        "catalog/supplier_product_cost_list.html",
        {
            "costs": costs,
            "query": query,
            "cost_count": costs.count(),
        },
    )


def _supplier_product_cost_form_view(request, *, instance, mode):
    old_value = _model_snapshot(instance, SupplierProductCostForm.Meta.fields)
    form = SupplierProductCostForm(request.POST or None, instance=instance)
    if request.method == "POST" and form.is_valid():
        cost = form.save()
        create_audit_log(
            action=AuditLog.Action.COST_CHANGE,
            module="catalog",
            user=request.user,
            request=request,
            object_type="SupplierProductCost",
            object_id=cost.pk,
            object_display=str(cost),
            old_value=old_value,
            new_value=_model_snapshot(cost, SupplierProductCostForm.Meta.fields),
        )
        messages.success(request, "Supplier reference cost was saved.")
        return redirect("supplier-product-cost-list")
    return render(
        request,
        "catalog/supplier_product_cost_form.html",
        {
            "form": form,
            "mode": mode,
            "object": instance,
        },
    )


@admin_required
@costs_required
def supplier_product_cost_create_view(request):
    return _supplier_product_cost_form_view(request, instance=None, mode="create")


@admin_required
@costs_required
def supplier_product_cost_edit_view(request, cost_id):
    cost = get_object_or_404(SupplierProductCost, pk=cost_id)
    return _supplier_product_cost_form_view(request, instance=cost, mode="edit")
