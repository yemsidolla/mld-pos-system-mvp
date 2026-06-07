from django.contrib.auth.signals import user_logged_in, user_login_failed
from django.dispatch import receiver

from .models import AuditLog
from .services import create_audit_log


@receiver(user_logged_in)
def log_login_success(sender, request, user, **kwargs):
    create_audit_log(
        action=AuditLog.Action.LOGIN_SUCCESS,
        module="accounts",
        user=user,
        request=request,
        object_type=user.__class__.__name__,
        object_id=user.pk,
        object_display=user.get_username(),
    )


@receiver(user_login_failed)
def log_login_failed(sender, credentials, request, **kwargs):
    username = credentials.get("username", "") if credentials else ""
    create_audit_log(
        action=AuditLog.Action.LOGIN_FAILED,
        module="accounts",
        request=request,
        object_type="User",
        object_display=username,
    )
