from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.urls import reverse

from accounts.models import StaffProfile
from audit.models import AuditLog
from core.permissions import (
    ADMIN_GROUP,
    CASHIER_GROUP,
    ROLE_CASHIER,
    ROLE_INVENTORY,
    ROLE_MANAGER,
    ROLE_OWNER,
    ROLE_VIEWER,
    can_access_pos,
    can_manage_inventory,
    can_manage_users,
    can_reset_data,
    can_view_reports,
    get_user_role,
    is_admin_user,
    is_cashier_user,
    is_inventory_staff,
)


class RoleTests(TestCase):
    def test_default_roles_exist_after_migrations(self):
        self.assertTrue(Group.objects.filter(name=ADMIN_GROUP).exists())
        self.assertTrue(Group.objects.filter(name=CASHIER_GROUP).exists())

    def test_admin_role_allows_admin_checks(self):
        user = get_user_model().objects.create_user(username="manager", password="Admin123", is_staff=True)
        user.groups.add(Group.objects.get(name=ADMIN_GROUP))

        self.assertTrue(is_admin_user(user))
        self.assertTrue(can_access_pos(user))

    def test_cashier_role_allows_pos_only(self):
        user = get_user_model().objects.create_user(username="cashier", password="Admin123")
        user.groups.add(Group.objects.get(name=CASHIER_GROUP))

        self.assertTrue(is_cashier_user(user))
        self.assertTrue(can_access_pos(user))
        self.assertFalse(is_admin_user(user))

    def test_cashier_is_blocked_from_django_admin_even_if_staff(self):
        user = get_user_model().objects.create_user(username="cashier", password="Admin123", is_staff=True)
        user.groups.add(Group.objects.get(name=CASHIER_GROUP))
        self.client.force_login(user)

        response = self.client.get(reverse("admin:index"))

        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "Access denied", status_code=403)

    def test_set_user_role_assigns_dashboard_admin_without_django_admin(self):
        user = get_user_model().objects.create_user(username="manager", password="Admin123", is_staff=False)

        call_command("set_user_role", "manager", "admin")
        user.refresh_from_db()

        self.assertTrue(user.groups.filter(name=ADMIN_GROUP).exists())
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertTrue(is_admin_user(user))

    def test_set_user_role_can_grant_django_admin_to_admin_role(self):
        user = get_user_model().objects.create_user(username="owner", password="Admin123", is_staff=False)

        call_command("set_user_role", "owner", "admin", "--django-admin")
        user.refresh_from_db()

        self.assertTrue(user.groups.filter(name=ADMIN_GROUP).exists())
        self.assertTrue(user.is_staff)

    def test_set_user_role_assigns_cashier_and_removes_staff(self):
        user = get_user_model().objects.create_user(username="cashier2", password="Admin123", is_staff=True)
        user.groups.add(Group.objects.get(name=ADMIN_GROUP))

        call_command("set_user_role", "cashier2", "cashier")
        user.refresh_from_db()

        self.assertTrue(user.groups.filter(name=CASHIER_GROUP).exists())
        self.assertFalse(user.groups.filter(name=ADMIN_GROUP).exists())
        self.assertFalse(user.is_staff)
        self.assertTrue(is_cashier_user(user))

    def test_set_user_role_rejects_django_admin_for_cashier(self):
        get_user_model().objects.create_user(username="cashier3", password="Admin123")

        with self.assertRaises(CommandError):
            call_command("set_user_role", "cashier3", "cashier", "--django-admin")

    def test_setup_roles_can_create_development_superuser(self):
        call_command("setup_roles", "--admin-username", "admin", "--password", "Admin123")

        user = get_user_model().objects.get(username="admin")
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.check_password("Admin123"))
        self.assertTrue(user.groups.filter(name=ADMIN_GROUP).exists())

    def test_set_user_role_assigns_inventory_profile_without_groups(self):
        user = get_user_model().objects.create_user(username="invuser", password="Admin123")

        call_command("set_user_role", "invuser", "inventory")
        user.refresh_from_db()

        self.assertEqual(user.staff_profile.role, ROLE_INVENTORY)
        self.assertFalse(user.groups.exists())
        self.assertFalse(user.is_staff)

    def test_set_user_role_admin_alias_sets_manager_profile(self):
        user = get_user_model().objects.create_user(username="legacy", password="Admin123")

        call_command("set_user_role", "legacy", "admin")
        user.refresh_from_db()

        self.assertEqual(user.staff_profile.role, ROLE_MANAGER)
        self.assertTrue(is_admin_user(user))


def _profile_user(username, role, **kwargs):
    user = get_user_model().objects.create_user(username=username, password="Admin123", **kwargs)
    StaffProfile.objects.create(user=user, role=role)
    return user


class StaffRoleResolutionTests(TestCase):
    def test_superuser_is_owner_even_without_profile(self):
        user = get_user_model().objects.create_user(
            username="su", password="Admin123", is_superuser=True, is_staff=True
        )
        self.assertEqual(get_user_role(user), ROLE_OWNER)

    def test_profile_role_is_used(self):
        user = _profile_user("inv", ROLE_INVENTORY)
        self.assertEqual(get_user_role(user), ROLE_INVENTORY)
        self.assertTrue(is_inventory_staff(user))

    def test_legacy_admin_group_maps_to_manager(self):
        user = get_user_model().objects.create_user(username="legacy-admin", password="Admin123")
        user.groups.add(Group.objects.get_or_create(name=ADMIN_GROUP)[0])
        self.assertEqual(get_user_role(user), ROLE_MANAGER)
        self.assertTrue(is_admin_user(user))

    def test_unassigned_user_has_no_role(self):
        user = get_user_model().objects.create_user(username="nobody", password="Admin123")
        self.assertIsNone(get_user_role(user))

    def test_inactive_user_with_profile_has_no_role(self):
        user = _profile_user("off", ROLE_OWNER, is_active=False)
        self.assertIsNone(get_user_role(user))

    def test_capability_matrix(self):
        owner = _profile_user("o", ROLE_OWNER)
        manager = _profile_user("m", ROLE_MANAGER)
        inventory = _profile_user("i", ROLE_INVENTORY)
        cashier = _profile_user("c", ROLE_CASHIER)
        viewer = _profile_user("v", ROLE_VIEWER)

        self.assertTrue(can_manage_users(owner) and can_manage_users(manager))
        self.assertFalse(any(can_manage_users(u) for u in (inventory, cashier, viewer)))
        self.assertTrue(can_manage_inventory(inventory))
        self.assertFalse(can_manage_inventory(cashier) or can_manage_inventory(viewer))
        self.assertTrue(can_view_reports(viewer))
        self.assertFalse(can_view_reports(cashier) or can_view_reports(inventory))
        self.assertTrue(can_access_pos(cashier))
        self.assertFalse(can_access_pos(inventory) or can_access_pos(viewer))
        self.assertTrue(can_reset_data(owner))
        self.assertFalse(any(can_reset_data(u) for u in (manager, inventory, cashier, viewer)))


class ReGatedAccessTests(TestCase):
    def test_inventory_staff_can_open_stock_pages_only(self):
        self.client.force_login(_profile_user("inv", ROLE_INVENTORY))
        self.assertEqual(self.client.get(reverse("dashboard-home")).status_code, 200)
        self.assertEqual(self.client.get(reverse("stock-in")).status_code, 200)
        self.assertEqual(self.client.get(reverse("inventory-summary")).status_code, 200)
        self.assertEqual(self.client.get(reverse("barcode-print")).status_code, 200)
        self.assertEqual(self.client.get(reverse("product-list")).status_code, 403)
        self.assertEqual(self.client.get(reverse("reports-index")).status_code, 403)
        self.assertEqual(self.client.get(reverse("pos-sale")).status_code, 403)

    def test_viewer_can_open_reports_and_sales_only(self):
        self.client.force_login(_profile_user("vw", ROLE_VIEWER))
        self.assertEqual(self.client.get(reverse("dashboard-home")).status_code, 200)
        self.assertEqual(self.client.get(reverse("reports-index")).status_code, 200)
        self.assertEqual(self.client.get(reverse("sales-history")).status_code, 200)
        self.assertEqual(self.client.get(reverse("stock-in")).status_code, 403)
        self.assertEqual(self.client.get(reverse("pos-sale")).status_code, 403)

    def test_cashier_keeps_pos_only(self):
        self.client.force_login(_profile_user("csh", ROLE_CASHIER))
        self.assertEqual(self.client.get(reverse("pos-sale")).status_code, 200)
        self.assertEqual(self.client.get(reverse("reports-index")).status_code, 403)
        self.assertEqual(self.client.get(reverse("stock-in")).status_code, 403)


class UserManagementTests(TestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user(
            username="owner", password="Admin123", is_superuser=True, is_staff=True
        )

    def test_owner_can_open_user_list_but_cashier_cannot(self):
        self.client.force_login(self.owner)
        self.assertEqual(self.client.get(reverse("user-list")).status_code, 200)

        self.client.force_login(_profile_user("cashier", ROLE_CASHIER))
        self.assertEqual(self.client.get(reverse("user-list")).status_code, 403)

    def test_create_user_assigns_role_group_and_audit(self):
        self.client.force_login(self.owner)
        response = self.client.post(
            reverse("user-create"),
            {
                "username": "newcashier",
                "first_name": "New",
                "email": "",
                "role": ROLE_CASHIER,
                "password": "StrongPass123",
            },
        )

        self.assertRedirects(response, reverse("user-list"))
        user = get_user_model().objects.get(username="newcashier")
        self.assertEqual(user.staff_profile.role, ROLE_CASHIER)
        self.assertTrue(user.groups.filter(name=CASHIER_GROUP).exists())
        self.assertTrue(
            AuditLog.objects.filter(
                action=AuditLog.Action.CREATE, module="accounts", object_id=str(user.pk)
            ).exists()
        )

    def test_role_change_is_audited(self):
        self.client.force_login(self.owner)
        staff = _profile_user("staff", ROLE_CASHIER)

        response = self.client.post(
            reverse("user-edit", kwargs={"user_id": staff.id}),
            {"first_name": "", "email": "", "role": ROLE_INVENTORY, "is_active": "on", "new_password": ""},
        )

        self.assertRedirects(response, reverse("user-list"))
        staff.refresh_from_db()
        self.assertEqual(staff.staff_profile.role, ROLE_INVENTORY)
        self.assertTrue(
            AuditLog.objects.filter(action=AuditLog.Action.ROLE_CHANGE, object_id=str(staff.pk)).exists()
        )

    def test_manager_cannot_assign_owner_role(self):
        self.client.force_login(_profile_user("mgr", ROLE_MANAGER))
        response = self.client.post(
            reverse("user-create"),
            {"username": "wannabe", "first_name": "", "email": "", "role": ROLE_OWNER, "password": "StrongPass123"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(get_user_model().objects.filter(username="wannabe").exists())

    def test_manager_cannot_edit_owner(self):
        self.client.force_login(_profile_user("mgr2", ROLE_MANAGER))
        owner2 = _profile_user("owner2", ROLE_OWNER)

        response = self.client.get(reverse("user-edit", kwargs={"user_id": owner2.id}))

        self.assertEqual(response.status_code, 403)

    def test_owner_cannot_disable_own_account(self):
        owner2 = _profile_user("owner2", ROLE_OWNER)
        self.client.force_login(owner2)

        response = self.client.post(
            reverse("user-edit", kwargs={"user_id": owner2.id}),
            {"first_name": "", "email": "", "role": ROLE_OWNER, "new_password": ""},
        )

        owner2.refresh_from_db()
        self.assertTrue(owner2.is_active)
        self.assertContains(response, "cannot disable your own account")

    def test_active_owner_count_counts_superusers_and_profile_owners(self):
        from accounts.views import _active_owner_count

        _profile_user("po", ROLE_OWNER)
        get_user_model().objects.create_user(
            username="disabled-su", password="Admin123", is_superuser=True, is_staff=True, is_active=False
        )

        # self.owner (active superuser) + po (active profile owner) = 2; disabled superuser excluded.
        self.assertEqual(_active_owner_count(), 2)
