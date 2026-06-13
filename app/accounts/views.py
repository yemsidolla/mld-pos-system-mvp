from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.db import models, transaction
from django.shortcuts import get_object_or_404, redirect, render

from audit.models import AuditLog
from audit.services import create_audit_log
from core.permissions import (
    ROLE_CASHIER,
    ROLE_LABELS,
    ROLE_OWNER,
    get_user_role,
    is_owner,
    users_required,
)

from .forms import StaffUserCreateForm, StaffUserEditForm, assignable_role_choices
from .services import set_role as _set_role, sync_legacy_group as _sync_legacy_group

User = get_user_model()
MODULE = "accounts"


def _active_owner_count(exclude_pk=None):
    qs = (
        User.objects.filter(is_active=True)
        .filter(models.Q(is_superuser=True) | models.Q(staff_profile__role=ROLE_OWNER))
        .distinct()
    )
    if exclude_pk is not None:
        qs = qs.exclude(pk=exclude_pk)
    return qs.count()


@users_required
def user_list_view(request):
    users = User.objects.select_related("staff_profile").order_by("username")
    rows = []
    for user in users:
        role = get_user_role(user)
        rows.append(
            {
                "user": user,
                "role": role,
                "role_label": ROLE_LABELS.get(role, "—"),
                "is_superuser": user.is_superuser,
            }
        )
    return render(request, "accounts/user_list.html", {"rows": rows})


@users_required
def user_create_view(request):
    request_is_owner = is_owner(request.user)
    form = StaffUserCreateForm(request.POST or None, allowed_roles=assignable_role_choices(request_is_owner))

    if request.method == "POST" and form.is_valid():
        role = form.cleaned_data["role"]
        if role == ROLE_OWNER and not request_is_owner:
            messages.error(request, "Only an Owner can assign the Owner role.")
        else:
            with transaction.atomic():
                user = User(
                    username=form.cleaned_data["username"],
                    first_name=form.cleaned_data["first_name"],
                    email=form.cleaned_data["email"],
                    is_active=True,
                )
                user.set_password(form.cleaned_data["password"])
                user.save()
                _set_role(user, role)
                _sync_legacy_group(user, role)
                create_audit_log(
                    action=AuditLog.Action.CREATE,
                    module=MODULE,
                    request=request,
                    object_type="User",
                    object_id=user.pk,
                    object_display=user.username,
                    new_value={"role": role, "is_active": True},
                )
            messages.success(request, f"User '{user.username}' was created.")
            return redirect("user-list")

    return render(
        request,
        "accounts/user_form.html",
        {"form": form, "mode": "create", "request_is_owner": request_is_owner},
    )


@users_required
def user_edit_view(request, user_id):
    target = get_object_or_404(User.objects.select_related("staff_profile"), pk=user_id)
    request_is_owner = is_owner(request.user)
    target_role = get_user_role(target)
    target_is_owner = target.is_superuser or target_role == ROLE_OWNER
    is_self = target.pk == request.user.pk

    # A Manager may not modify an Owner or a Django superuser.
    if target_is_owner and not request_is_owner:
        raise PermissionDenied

    # Always include the target's current role so it shows even if the editor
    # could not otherwise assign it.
    allowed = assignable_role_choices(request_is_owner)
    if target_role and target_role not in {slug for slug, _ in allowed}:
        allowed = allowed + [(target_role, ROLE_LABELS.get(target_role, target_role))]

    form = StaffUserEditForm(
        request.POST or None,
        allowed_roles=allowed,
        initial={
            "first_name": target.first_name,
            "email": target.email,
            "role": target_role or ROLE_CASHIER,
            "is_active": target.is_active,
        },
    )

    if request.method == "POST" and form.is_valid():
        new_role = form.cleaned_data["role"]
        new_active = form.cleaned_data["is_active"]
        errors = []

        if new_role == ROLE_OWNER and not request_is_owner:
            errors.append("Only an Owner can assign the Owner role.")
        if is_self and new_role != target_role:
            errors.append("You cannot change your own role.")
        if is_self and not new_active:
            errors.append("You cannot disable your own account.")

        will_remain_owner = new_active and (target.is_superuser or new_role == ROLE_OWNER)
        if target_is_owner and not will_remain_owner and _active_owner_count(exclude_pk=target.pk) == 0:
            errors.append("At least one active Owner must remain.")

        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            with transaction.atomic():
                old_value = {"role": target_role, "is_active": target.is_active}
                target.first_name = form.cleaned_data["first_name"]
                target.email = form.cleaned_data["email"]
                target.is_active = new_active
                update_fields = ["first_name", "email", "is_active"]
                if form.cleaned_data["new_password"]:
                    target.set_password(form.cleaned_data["new_password"])
                    update_fields.append("password")
                target.save(update_fields=update_fields)
                _set_role(target, new_role)
                _sync_legacy_group(target, new_role)

                create_audit_log(
                    action=AuditLog.Action.UPDATE,
                    module=MODULE,
                    request=request,
                    object_type="User",
                    object_id=target.pk,
                    object_display=target.username,
                    old_value=old_value,
                    new_value={"role": new_role, "is_active": new_active},
                )
                if new_role != target_role:
                    create_audit_log(
                        action=AuditLog.Action.ROLE_CHANGE,
                        module=MODULE,
                        request=request,
                        object_type="User",
                        object_id=target.pk,
                        object_display=target.username,
                        old_value={"role": target_role},
                        new_value={"role": new_role},
                    )
                if old_value["is_active"] and not new_active:
                    create_audit_log(
                        action=AuditLog.Action.DEACTIVATE,
                        module=MODULE,
                        request=request,
                        object_type="User",
                        object_id=target.pk,
                        object_display=target.username,
                    )
            messages.success(request, f"User '{target.username}' was updated.")
            return redirect("user-list")

    return render(
        request,
        "accounts/user_form.html",
        {
            "form": form,
            "mode": "edit",
            "target": target,
            "target_role": target_role,
            "target_role_label": ROLE_LABELS.get(target_role, "—"),
            "request_is_owner": request_is_owner,
            "is_self": is_self,
        },
    )
