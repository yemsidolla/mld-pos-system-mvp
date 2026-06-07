from django.contrib.auth.models import AnonymousUser

from .models import AuditLog


def get_client_ip(request):
    if request is None:
        return None

    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    return request.META.get("REMOTE_ADDR")


def get_user_agent(request):
    if request is None:
        return ""
    return request.META.get("HTTP_USER_AGENT", "")


def resolve_user(user):
    if user is None or isinstance(user, AnonymousUser) or not user.is_authenticated:
        return None
    return user


def create_audit_log(
    *,
    action,
    module,
    user=None,
    request=None,
    object_type="",
    object_id="",
    object_display="",
    old_value=None,
    new_value=None,
):
    if request is not None and user is None:
        user = getattr(request, "user", None)

    return AuditLog.objects.create(
        user=resolve_user(user),
        action=action,
        module=module,
        object_type=object_type,
        object_id=str(object_id) if object_id not in (None, "") else "",
        object_display=str(object_display) if object_display not in (None, "") else "",
        old_value=old_value,
        new_value=new_value,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
    )
