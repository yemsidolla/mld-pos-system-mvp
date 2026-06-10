from django.shortcuts import render

from core.pagination import paginate
from core.permissions import audit_required

from .forms import AuditLogFilterForm
from .models import AuditLog


@audit_required
def audit_log_list_view(request):
    """Read-only audit trail for Owner/Manager.

    There is intentionally no create/update/delete path here: the audit log is
    immutable from the dashboard. Records are still only written by
    ``audit.services.create_audit_log``.
    """
    form = AuditLogFilterForm(request.GET or None)
    logs = form.filter(AuditLog.objects.select_related("user").all())

    page_obj, querystring = paginate(request, logs)

    return render(
        request,
        "audit/audit_log_list.html",
        {
            "form": form,
            "page_obj": page_obj,
            "total_count": page_obj.paginator.count,
            "querystring": querystring,
        },
    )
