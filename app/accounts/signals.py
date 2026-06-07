from django.contrib.auth.models import Group
from django.db.models.signals import post_migrate
from django.dispatch import receiver

from core.permissions import ADMIN_GROUP, CASHIER_GROUP


@receiver(post_migrate)
def create_default_roles(sender, **kwargs):
    Group.objects.get_or_create(name=ADMIN_GROUP)
    Group.objects.get_or_create(name=CASHIER_GROUP)
