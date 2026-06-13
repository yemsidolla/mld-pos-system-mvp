from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from core.permissions import catalog_required

from .forms import BatchUploadForm
from .models import BatchUploadJob, BatchUploadRow
from .services import (
    commit_upload_job,
    create_upload_job,
    delete_upload_row,
    get_schema,
    get_template_csv,
    update_upload_row,
)


def get_row_status(row):
    if row.is_deleted:
        return "Deleted"
    if not row.is_selected:
        return "Skipped"
    if row.validation_errors:
        return "Invalid"
    if row.warnings:
        return "Warning"
    return "Valid"


@catalog_required
def batch_upload_index_view(request):
    form = BatchUploadForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        try:
            job = create_upload_job(
                target=form.cleaned_data["target"],
                uploaded_file=form.cleaned_data["file"],
                uploaded_by=request.user,
            )
        except ValidationError as exc:
            form.add_error(None, exc)
        else:
            messages.success(request, "Upload parsed. Review the preview before committing.")
            return redirect("batch-upload-detail", job_id=job.id)

    jobs = BatchUploadJob.objects.select_related("uploaded_by").order_by("-created_at")[:25]
    return render(
        request,
        "batch_upload/index.html",
        {
            "form": form,
            "jobs": jobs,
            "targets": BatchUploadJob.Target.choices,
        },
    )


@catalog_required
def batch_upload_detail_view(request, job_id):
    job = get_object_or_404(BatchUploadJob.objects.select_related("uploaded_by"), pk=job_id)
    fields = get_schema(job.target)["fields"]
    rows = list(job.rows.all())
    row_view_models = [{"row": row, "status": get_row_status(row)} for row in rows]
    counts = {
        "valid": sum(1 for row in rows if row.can_commit),
        "invalid": sum(1 for row in rows if row.is_selected and not row.is_deleted and row.validation_errors),
        "deleted": sum(1 for row in rows if row.is_deleted),
        "rows": len(rows),
    }
    return render(
        request,
        "batch_upload/detail.html",
        {
            "job": job,
            "fields": fields,
            "row_view_models": row_view_models,
            "counts": counts,
        },
    )


@catalog_required
def batch_upload_row_update_view(request, job_id, row_id):
    row = get_object_or_404(BatchUploadRow.objects.select_related("job"), pk=row_id, job_id=job_id)
    if request.method == "POST":
        try:
            update_upload_row(row, request.POST)
        except ValidationError as exc:
            messages.error(request, "; ".join(exc.messages))
        else:
            messages.success(request, f"Row {row.row_number} updated.")
    return redirect("batch-upload-detail", job_id=job_id)


@catalog_required
def batch_upload_row_delete_view(request, job_id, row_id):
    row = get_object_or_404(BatchUploadRow.objects.select_related("job"), pk=row_id, job_id=job_id)
    if request.method == "POST":
        try:
            delete_upload_row(row)
        except ValidationError as exc:
            messages.error(request, "; ".join(exc.messages))
        else:
            messages.success(request, f"Row {row.row_number} deleted from commit preview.")
    return redirect("batch-upload-detail", job_id=job_id)


@catalog_required
def batch_upload_commit_view(request, job_id):
    job = get_object_or_404(BatchUploadJob, pk=job_id)
    if request.method == "POST":
        try:
            commit_upload_job(job=job, committed_by=request.user, request=request)
        except ValidationError as exc:
            messages.error(request, "; ".join(exc.messages))
        else:
            messages.success(request, "Upload committed.")
    return redirect("batch-upload-detail", job_id=job_id)


@catalog_required
def batch_upload_template_view(request, target):
    try:
        csv_content = get_template_csv(target)
    except ValidationError as exc:
        raise Http404("Upload template not found.") from exc
    response = HttpResponse(csv_content, content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{target}_template.csv"'
    return response
