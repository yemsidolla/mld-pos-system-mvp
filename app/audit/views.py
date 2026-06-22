from django.shortcuts import render

from core.pagination import paginate
from core.permissions import audit_required

from .forms import AuditLogFilterForm
from .models import AuditLog


RISK_ACTIONS = {
    AuditLog.Action.SALE_CANCEL,
    AuditLog.Action.BELOW_COST_SALE,
    AuditLog.Action.SALE_OVERRIDE,
    AuditLog.Action.PROMOTION_BELOW_COST_SALE,
    AuditLog.Action.STOCK_ADJUSTMENT,
    AuditLog.Action.STOCK_BATCH_COST_CHANGE,
    AuditLog.Action.COST_CHANGE,
    AuditLog.Action.ROLE_CHANGE,
    AuditLog.Action.SETTING_CHANGE,
    AuditLog.Action.DATA_RESET,
    AuditLog.Action.PERMISSION_DENIED,
}


@audit_required
def audit_log_list_view(request):
    """Read-only audit trail for Owner/Manager.

    There is intentionally no create/update/delete path here: the audit log is
    immutable from the dashboard. Records are still only written by
    ``audit.services.create_audit_log``.
    """
    form = AuditLogFilterForm(request.GET or None)
    logs = form.filter(AuditLog.objects.select_related("user").all())
    summary = {
        "total_count": logs.count(),
        "risk_count": logs.filter(action__in=RISK_ACTIONS).count(),
        "module_count": logs.exclude(module="").values("module").distinct().count(),
        "user_count": logs.exclude(user__isnull=True).values("user").distinct().count(),
    }

    page_obj, querystring = paginate(request, logs)
    for log in page_obj.object_list:
        log.is_risk_action = log.action in RISK_ACTIONS

    return render(
        request,
        "audit/audit_log_list.html",
        {
            "form": form,
            "page_obj": page_obj,
            "total_count": page_obj.paginator.count,
            "summary": summary,
            "querystring": querystring,
        },
    )
