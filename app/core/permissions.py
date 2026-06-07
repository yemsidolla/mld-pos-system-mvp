from django.contrib.auth.decorators import user_passes_test


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


def admin_required(view_func):
    return user_passes_test(is_admin_user)(view_func)


def pos_required(view_func):
    return user_passes_test(can_access_pos)(view_func)
