from .permissions import dashboard_access_denied_response, is_cashier_user, is_admin_user


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
            return dashboard_access_denied_response(request)
        return self.get_response(request)
