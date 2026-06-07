from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from core.permissions import ADMIN_GROUP, CASHIER_GROUP, can_access_pos, is_admin_user, is_cashier_user


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
