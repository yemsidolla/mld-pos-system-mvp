"""Development-only authentication bypass.

**This is a deliberate auth backdoor. It exists to let a developer (or an agent
doing a UX pass) browse the dashboard on a LOCAL instance without logging in.**

It is wired into ``MIDDLEWARE`` by ``settings.py`` ONLY when both:

- ``DJANGO_DEBUG`` is true, and
- ``DEV_AUTH_BYPASS`` is true.

``settings.py`` additionally **refuses to start** if ``DEV_AUTH_BYPASS`` is set
while ``DEBUG`` is false, or while a public production/SIT host is in
``ALLOWED_HOSTS``. Production and SIT run with ``DEBUG=False``, so this can never
activate there — a misconfiguration crashes the process instead of silently
opening the door. Fail closed, loudly.

Never set ``DEV_AUTH_BYPASS=True`` in a production or SIT ``.env``.
"""

import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import MiddlewareNotUsed

logger = logging.getLogger(__name__)


class DevAuthBypassMiddleware:
    """Force every request to be authenticated as a fixed dev user.

    Self-disables via ``MiddlewareNotUsed`` unless the two-flag condition holds,
    so even if it is wired in by mistake it does nothing when inactive.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        if not (settings.DEBUG and getattr(settings, "DEV_AUTH_BYPASS", False)):
            # Belt-and-suspenders: refuse to install when not explicitly active.
            raise MiddlewareNotUsed
        self._username = getattr(settings, "DEV_AUTH_BYPASS_USER", "") or ""
        logger.warning(
            "DEV AUTH BYPASS ACTIVE — every request is authenticated without a "
            "password. This must only ever run on a local dev instance."
        )

    def __call__(self, request):
        if not request.user.is_authenticated:
            user = self._resolve_user()
            if user is not None:
                request.user = user
        return self.get_response(request)

    def _resolve_user(self):
        User = get_user_model()
        qs = User.objects.filter(is_active=True)
        if self._username:
            return qs.filter(username=self._username).first()
        return qs.filter(is_superuser=True).order_by("pk").first()
