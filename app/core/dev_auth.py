"""Development-only authentication bypass.

**This is a deliberate auth backdoor.** It authenticates every request as a dev
user so the dashboard can be browsed without logging in on a LOCAL instance
(UX passes, automated browsing).

Activation is gated by a single source of truth, ``dev_auth_bypass_active``,
called by both ``settings.py`` (to decide whether to install the middleware) and
the tests (so the guard cannot be weakened without failing a test).

The gate is an **allowlist**, not a denylist: it activates only when every host
in ``ALLOWED_HOSTS`` is a loopback host. A wildcard, a public IP, or any real
domain refuses to boot. A denylist of production domains was the original design
and was unsafe — ``['*']`` passed it. Do not reintroduce one.

Never set ``DEV_AUTH_BYPASS=True`` in a production or SIT ``.env``. If it is set
there, the process refuses to start rather than opening the door.
"""

import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured, MiddlewareNotUsed

logger = logging.getLogger(__name__)

# The ONLY hosts for which the bypass may activate. Anything else — a real
# domain, a public IP, or "*" — means this is not a local dev process.
LOCAL_ONLY_HOSTS = frozenset({"localhost", "127.0.0.1", "::1", "0.0.0.0", "web", "testserver"})


def dev_auth_bypass_active(debug, dev_auth_bypass, allowed_hosts):
    """Single source of truth for whether the bypass may run.

    Returns ``False`` when the bypass is simply off. Raises
    ``ImproperlyConfigured`` — refusing to boot — when the bypass is requested in
    any context that is not a strictly local dev process. Returns ``True`` only
    for a local dev process.
    """
    if not dev_auth_bypass:
        return False

    if not debug:
        raise ImproperlyConfigured(
            "DEV_AUTH_BYPASS=True requires DJANGO_DEBUG=True. Refusing to start — "
            "this must never run in production or SIT."
        )

    # Normalise: strip whitespace, lowercase, drop a trailing dot (all of which
    # are otherwise valid ways to express the same host).
    hosts = [h.strip().lower().rstrip(".") for h in allowed_hosts if h.strip()]
    if not hosts:
        raise ImproperlyConfigured(
            "DEV_AUTH_BYPASS=True requires an explicit loopback-only "
            "DJANGO_ALLOWED_HOSTS. Refusing to start."
        )

    non_local = [h for h in hosts if h not in LOCAL_ONLY_HOSTS]
    if non_local:
        raise ImproperlyConfigured(
            "DEV_AUTH_BYPASS=True only runs when every ALLOWED_HOSTS entry is a "
            f"loopback host. Refusing to start — non-local hosts present: {non_local}. "
            "A wildcard '*' is rejected for the same reason."
        )

    return True


class DevAuthBypassMiddleware:
    """Force every request to be authenticated as a fixed dev user.

    Self-disables via ``MiddlewareNotUsed`` unless ``dev_auth_bypass_active``
    agrees, so even if it is wired in by mistake it does nothing when inactive.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        active = dev_auth_bypass_active(
            settings.DEBUG,
            getattr(settings, "DEV_AUTH_BYPASS", False),
            settings.ALLOWED_HOSTS,
        )
        if not active:
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
        # On lookup failure the exception propagates and the request fails
        # unauthenticated — fail closed, never fail open.
        User = get_user_model()
        qs = User.objects.filter(is_active=True)
        if self._username:
            return qs.filter(username=self._username).first()
        return qs.filter(is_superuser=True).order_by("pk").first()
