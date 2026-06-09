from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from audit.models import AuditLog
from audit.services import create_audit_log
from catalog.models import Product
from core.permissions import admin_required, inventory_required
from pos.pricing import calculate_promotion_price

from .forms import LabelPrintForm, LabelTemplateForm, PromotionLabelForm
from .models import LabelTemplate

MODULE = "labels"


def products_for_promotion(promotion):
    if promotion.product_id:
        return [promotion.product] if promotion.product.is_active else []
    if promotion.category_id:
        return list(
            Product.objects.filter(category_id=promotion.category_id, is_active=True).order_by("name")
        )
    return []


@admin_required
def label_template_list_view(request):
    templates = LabelTemplate.objects.all()
    return render(request, "labels/template_list.html", {"templates": templates})


@admin_required
def label_template_create_view(request):
    form = LabelTemplateForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        template = form.save()
        create_audit_log(
            action=AuditLog.Action.CREATE,
            module=MODULE,
            request=request,
            object_type="LabelTemplate",
            object_id=template.pk,
            object_display=template.name,
            new_value={"name": template.name, "template_type": template.template_type},
        )
        messages.success(request, f"Label template '{template.name}' was created.")
        return redirect("label-template-list")
    return render(request, "labels/template_form.html", {"form": form, "mode": "create"})


@admin_required
def label_template_edit_view(request, template_id):
    template = get_object_or_404(LabelTemplate, pk=template_id)
    form = LabelTemplateForm(request.POST or None, instance=template)
    if request.method == "POST" and form.is_valid():
        template = form.save()
        create_audit_log(
            action=AuditLog.Action.UPDATE,
            module=MODULE,
            request=request,
            object_type="LabelTemplate",
            object_id=template.pk,
            object_display=template.name,
            new_value={"name": template.name, "template_type": template.template_type},
        )
        messages.success(request, f"Label template '{template.name}' was updated.")
        return redirect("label-template-list")
    return render(
        request,
        "labels/template_form.html",
        {"form": form, "mode": "edit", "template": template},
    )


@inventory_required
def label_print_view(request):
    form = LabelPrintForm(request.POST or None)
    context = {"form": form, "labels": [], "template": None, "auto_print": False}

    if request.method == "POST" and form.is_valid():
        template = form.cleaned_data["template"]
        quantity = form.cleaned_data["quantity"]
        batches = form.cleaned_data["stock_batches"]
        labels = []
        for batch in batches:
            for _ in range(quantity):
                labels.append(batch)
        context.update({"template": template, "labels": labels})

        if request.POST.get("action") == "print":
            context["auto_print"] = True
            create_audit_log(
                action=AuditLog.Action.BARCODE_PRINT,
                module=MODULE,
                request=request,
                object_type="LabelTemplate",
                object_id=template.pk,
                object_display=template.name,
                new_value={
                    "labels": len(labels),
                    "batches": [batch.batch_no for batch in batches],
                },
            )

    return render(request, "labels/label_print.html", context)


@inventory_required
def promotion_label_print_view(request):
    form = PromotionLabelForm(request.POST or None)
    context = {"form": form, "labels": [], "template": None, "auto_print": False, "promotion": None}

    if request.method == "POST" and form.is_valid():
        promotion = form.cleaned_data["promotion"]
        template = form.cleaned_data["template"]
        quantity = form.cleaned_data["quantity"]
        custom_text = form.cleaned_data["custom_text"]
        products = products_for_promotion(promotion)

        if not products:
            messages.error(request, "This promotion has no active products to label.")
        else:
            labels = []
            for product in products:
                price = calculate_promotion_price(promotion, product.default_selling_price)
                card = {
                    "product": product,
                    "original_price": price.original_unit_price,
                    "promo_price": price.final_unit_price,
                    "discount": price.discount_per_unit,
                    "custom_text": custom_text,
                }
                labels.extend([card] * quantity)
            context.update({"promotion": promotion, "template": template, "labels": labels})

            if request.POST.get("action") == "print":
                context["auto_print"] = True
                create_audit_log(
                    action=AuditLog.Action.BARCODE_PRINT,
                    module=MODULE,
                    request=request,
                    object_type="Promotion",
                    object_id=promotion.pk,
                    object_display=promotion.name,
                    new_value={
                        "labels": len(labels),
                        "template": template.name,
                        "products": [product.product_code for product in products],
                    },
                )

    return render(request, "labels/promotion_label_print.html", context)
