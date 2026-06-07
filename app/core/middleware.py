from django.http import HttpResponseForbidden

from .permissions import is_cashier_user, is_admin_user


class CashierAdminBlockMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (
            request.path.startswith("/admin/")
            and request.user.is_authenticated
            and is_cashier_user(request.user)
            and not is_admin_user(request.user)
        ):
            return HttpResponseForbidden("Cashier users cannot access Django Admin.")
        return self.get_response(request)
