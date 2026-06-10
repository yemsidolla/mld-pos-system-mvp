from django.core.paginator import Paginator
from django.shortcuts import render

from core.permissions import audit_required

from .forms import AuditLogFilterForm
from .models import AuditLog

PAGE_SIZE = 25


@audit_required
def audit_log_list_view(request):
    """Read-only audit trail for Owner/Manager.

    There is intentionally no create/update/delete path here: the audit log is
    immutable from the dashboard. Records are still only written by
    ``audit.services.create_audit_log``.
    """
    form = AuditLogFilterForm(request.GET or None)
    logs = AuditLog.objects.select_related("user").all()
    logs = form.filter(logs)

    paginator = Paginator(logs, PAGE_SIZE)
    page_obj = paginator.get_page(request.GET.get("page"))

    querystring = request.GET.copy()
    querystring.pop("page", None)

    return render(
        request,
        "audit/audit_log_list.html",
        {
            "form": form,
            "page_obj": page_obj,
            "total_count": paginator.count,
            "querystring": querystring.urlencode(),
        },
    )
