from functools import wraps

from django.conf import settings
from django.contrib.auth.views import redirect_to_login
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.cache import never_cache


# Legacy Django group names. Kept for backward compatibility ("map and keep"):
# accounts that predate the V4 StaffProfile model are still resolved through
# these groups.
ADMIN_GROUP = "Admin"
CASHIER_GROUP = "Cashier"

# V4 staff roles. These string values MUST match accounts.models.StaffProfile.Role.
ROLE_OWNER = "OWNER"
ROLE_MANAGER = "MANAGER"
ROLE_INVENTORY = "INVENTORY"
ROLE_CASHIER = "CASHIER"
ROLE_VIEWER = "VIEWER"

STAFF_ROLES = (ROLE_OWNER, ROLE_MANAGER, ROLE_INVENTORY, ROLE_CASHIER, ROLE_VIEWER)

ROLE_LABELS = {
    ROLE_OWNER: "Owner",
    ROLE_MANAGER: "Manager",
    ROLE_INVENTORY: "Inventory staff",
    ROLE_CASHIER: "Cashier",
    ROLE_VIEWER: "Viewer / Auditor",
}


def has_group(user, group_name):
    return user.is_authenticated and user.groups.filter(name=group_name).exists()


def get_user_role(user):
    """Resolve the effective staff role for ``user`` or ``None`` for no access.

    Resolution order, chosen so nobody can be accidentally locked out:

    1. Superusers are always Owner.
    2. An explicit ``StaffProfile`` wins next.
    3. Legacy ``Admin``/``Cashier`` group membership maps to Manager/Cashier.
    4. Otherwise the user has no dashboard access.
    """
    if user is None or not getattr(user, "is_authenticated", False) or not user.is_active:
        return None
    if user.is_superuser:
        return ROLE_OWNER
    profile = getattr(user, "staff_profile", None)
    if profile is not None and profile.role:
        return profile.role
    if has_group(user, ADMIN_GROUP):
        return ROLE_MANAGER
    if has_group(user, CASHIER_GROUP):
        return ROLE_CASHIER
    return None


def has_role(user, *roles):
    return get_user_role(user) in roles


def role_label(role):
    if role in ROLE_LABELS:
        return ROLE_LABELS[role]
    if not role:
        return ""
    from accounts.models import Role  # lazy: custom roles live in the DB

    found = Role.objects.filter(slug=role).first()
    return found.name if found else role


# --- Data-driven capabilities (Authz Phase 1) ------------------------------
# Roles grant capabilities as data (accounts.Role). The {slug: (is_owner, caps)}
# map is loaded once and cached on the request's user object, so each request
# does a single query and always sees current data — correct across multiple
# gunicorn workers, unlike a module-level cache.
def _roles_map(user=None):
    cached = getattr(user, "_melodu_roles_map", None)
    if cached is not None:
        return cached
    from accounts.models import Role  # lazy: avoid app-loading cycle

    try:
        data = {r.slug: (r.is_owner, set(r.capabilities or [])) for r in Role.objects.all()}
    except Exception:  # pragma: no cover - defensive (e.g. before migrations)
        return {}
    if user is not None:
        try:
            user._melodu_roles_map = data
        except (AttributeError, TypeError):  # pragma: no cover - e.g. None/immutable
            pass
    return data


def clear_role_capability_cache(user=None):
    """Drop the per-request role cache. Call after editing roles within a request
    so a subsequent capability check in the same request sees the change."""
    if user is not None and hasattr(user, "_melodu_roles_map"):
        del user._melodu_roles_map


def has_capability(user, capability):
    """True if ``user``'s effective role grants ``capability``.

    Owner-tier roles implicitly hold every capability. Resolution flows through
    ``get_user_role`` so superusers (always Owner) and the legacy group mapping
    keep working unchanged.
    """
    role = get_user_role(user)
    if role is None:
        return False
    info = _roles_map(user).get(role)
    if info is None:
        return False
    is_owner_role, capabilities = info
    return is_owner_role or capability in capabilities


# --- Role predicates -------------------------------------------------------
def is_owner(user):
    return has_role(user, ROLE_OWNER)


def is_manager(user):
    return has_role(user, ROLE_MANAGER)


def is_inventory_staff(user):
    return has_role(user, ROLE_INVENTORY)


def is_viewer(user):
    return has_role(user, ROLE_VIEWER)


# --- Backward-compatible predicates (behavior preserved) -------------------
def is_admin_user(user):
    """Legacy "Admin" capability: full management. Now Owner or Manager."""
    return has_role(user, ROLE_OWNER, ROLE_MANAGER)


def is_cashier_user(user):
    return has_role(user, ROLE_CASHIER)


def can_access_pos(user):
    return has_capability(user, "pos.access")


def can_access_dashboard(user):
    """Any user with a recognised role can open the dashboard shell."""
    return get_user_role(user) is not None


# --- Capability checks (now data-driven; see accounts.Role) -----------------
def can_manage_users(user):
    return has_capability(user, "system.manage_users")


def can_manage_catalog(user):
    return has_capability(user, "catalog.manage")


def can_manage_inventory(user):
    return has_capability(user, "inventory.manage")


def can_manage_promotions(user):
    return has_capability(user, "promotions.manage")


def can_view_sales_history(user):
    return has_capability(user, "sales.view_history")


def can_cancel_sale(user):
    return has_capability(user, "sales.cancel")


def can_view_reports(user):
    return has_capability(user, "reports.view")


def can_view_system(user):
    return has_capability(user, "system.view_logs")


def can_view_audit(user):
    """Read-only access to the audit trail."""
    return has_capability(user, "system.view_audit")


def can_manage_settings(user):
    return has_capability(user, "system.manage_settings")


def can_reset_data(user):
    """Owner-only by default. Used by the data-reset tooling."""
    return has_capability(user, "system.reset_data")


def can_reprint_sale(user):
    return has_capability(user, "sales.reprint")


def can_override_below_cost(user):
    return has_capability(user, "pos.override_below_cost")


def can_manage_roles(user):
    """Edit the role permission matrix — Owner tier only."""
    return is_owner(user)


def can_view_costs(user):
    """Cost/profit visibility, configurable per role in Store Settings.

    Owners always see costs (cannot be locked out). Other roles see them only
    while listed in ``StoreSetting.cost_visible_roles``.
    """
    role = get_user_role(user)
    if role is None:
        return False
    if role == ROLE_OWNER:
        return True
    from .models import StoreSetting  # local import: avoid app-loading cycle

    try:
        visible = StoreSetting.load().cost_visible_roles or []
    except Exception:  # pragma: no cover - defensive (e.g. before migrations)
        visible = []
    return role in visible


# --- Access-denied rendering & decorators ----------------------------------
def _log_permission_denied(request):
    # Imported lazily so core.permissions stays importable before apps load.
    from audit.models import AuditLog
    from audit.services import create_audit_log

    create_audit_log(
        action=AuditLog.Action.PERMISSION_DENIED,
        module="core",
        request=request,
        object_type="Path",
        object_display=request.path[:255],
        new_value={"method": request.method, "role": get_user_role(request.user)},
    )


def dashboard_access_denied_response(request):
    user = request.user
    title = "Access denied"
    message = "Your account does not have permission to open this area."
    if user.is_authenticated:
        _log_permission_denied(request)

    if user.is_authenticated and get_user_role(user) is None:
        title = "No role assigned"
        message = (
            "Your account is signed in but has no Melodu role yet. "
            "Ask an administrator to assign you a role, then log in again."
        )
        action_label = "Login again"
        action_url = reverse("dashboard-login")
        secondary_label = ""
        secondary_url = ""
    elif is_cashier_user(user) and not is_admin_user(user):
        action_label = "Back to POS"
        action_url = reverse("pos-sale")
        secondary_label = "Login again"
        secondary_url = reverse("dashboard-login")
    elif can_access_dashboard(user):
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
            "title": title,
            "message": message,
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


# Decorators per capability. ``admin_required`` and ``pos_required`` keep their
# original names and behavior so existing views and tests are unaffected.
def admin_required(view_func):
    return dashboard_role_required(is_admin_user)(view_func)


def pos_required(view_func):
    return dashboard_role_required(can_access_pos)(view_func)


def dashboard_required(view_func):
    return dashboard_role_required(can_access_dashboard)(view_func)


def users_required(view_func):
    return dashboard_role_required(can_manage_users)(view_func)


def inventory_required(view_func):
    return dashboard_role_required(can_manage_inventory)(view_func)


def reports_required(view_func):
    return dashboard_role_required(can_view_reports)(view_func)


def sales_history_required(view_func):
    return dashboard_role_required(can_view_sales_history)(view_func)


def system_required(view_func):
    return dashboard_role_required(can_view_system)(view_func)


def audit_required(view_func):
    return dashboard_role_required(can_view_audit)(view_func)


def settings_required(view_func):
    return dashboard_role_required(can_manage_settings)(view_func)


def costs_required(view_func):
    return dashboard_role_required(can_view_costs)(view_func)


def catalog_required(view_func):
    return dashboard_role_required(can_manage_catalog)(view_func)


def promotions_required(view_func):
    return dashboard_role_required(can_manage_promotions)(view_func)


def sales_cancel_required(view_func):
    return dashboard_role_required(can_cancel_sale)(view_func)


def sales_reprint_required(view_func):
    return dashboard_role_required(can_reprint_sale)(view_func)


def owner_required(view_func):
    return dashboard_role_required(can_manage_roles)(view_func)
