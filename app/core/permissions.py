from functools import wraps

from django.conf import settings
from django.contrib.auth.views import redirect_to_login
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.cache import never_cache


ADMIN_GROUP = "Admin"
CASHIER_GROUP = "Cashier"


def has_group(user, group_name):
    return user.is_authenticated and user.groups.filter(name=group_name).exists()


def is_admin_user(user):
    return user.is_authenticated and user.is_active and (user.is_superuser or has_group(user, ADMIN_GROUP))


def is_cashier_user(user):
    return user.is_authenticated and user.is_active and has_group(user, CASHIER_GROUP)


def can_access_pos(user):
    return is_admin_user(user) or is_cashier_user(user)


def dashboard_access_denied_response(request):
    user = request.user
    if can_access_pos(user):
        if is_cashier_user(user) and not is_admin_user(user):
            action_label = "Back to POS"
            action_url = reverse("pos-sale")
        else:
            action_label = "Back to Dashboard"
            action_url = reverse("dashboard-home")
        secondary_label = "Login again"
        secondary_url = reverse("dashboard-login")
    else:
        action_label = "Login again"
        action_url = reverse("dashboard-login")
        secondary_label = ""
        secondary_url = ""

    return render(
        request,
        "dashboard/error.html",
        {
            "status_code": "403",
            "title": "Access denied",
            "message": "Your account does not have permission to open this area.",
            "action_label": action_label,
            "action_url": action_url,
            "secondary_label": secondary_label,
            "secondary_url": secondary_url,
        },
        status=403,
    )


def dashboard_role_required(test_func):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path(), settings.LOGIN_URL)
            if not request.user.is_active or not test_func(request.user):
                return dashboard_access_denied_response(request)
            return view_func(request, *args, **kwargs)

        return never_cache(wrapped)

    return decorator


def admin_required(view_func):
    return dashboard_role_required(is_admin_user)(view_func)


def pos_required(view_func):
    return dashboard_role_required(can_access_pos)(view_func)
