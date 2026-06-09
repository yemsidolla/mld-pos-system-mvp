from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from audit.models import AuditLog
from audit.services import create_audit_log
from core.permissions import admin_required, inventory_required

from .forms import LabelPrintForm, LabelTemplateForm
from .models import LabelTemplate

MODULE = "labels"


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
