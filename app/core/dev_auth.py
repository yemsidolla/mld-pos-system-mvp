"""Development-only authentication bypass.

**This is a deliberate auth backdoor.** It authenticates every request as a dev
user so the dashboard can be browsed without logging in on a LOCAL instance
(UX passes, automated browsing).

Three independent controls must all hold before any request is bypassed:

1. **Startup allowlist** (``dev_auth_bypass_active``) — the process refuses to
   boot unless ``DEBUG`` is true and every ``ALLOWED_HOSTS`` entry is a loopback
   host. Production and SIT have public hosts, so they crash rather than open the
   door. This is the money-critical guarantee.
2. **Not under the test runner** — the middleware is not installed during
   ``manage.py test``, so a bypass-enabled ``.env`` cannot authenticate test
   clients.
3. **Per-request trusted peer** — the middleware only bypasses when the TCP peer
   (``REMOTE_ADDR``, set by the server, not the client-controlled ``Host``
   header) is in ``DEV_AUTH_BYPASS_TRUSTED_ADDRS``, which defaults to loopback.
   A remote client spoofing ``Host: localhost`` is not trusted and falls through
   to normal login.

The single gate ``dev_auth_bypass_active`` is called by both ``settings.py`` and
the tests, so it cannot be weakened without failing a test.

Never set ``DEV_AUTH_BYPASS=True`` in a production or SIT ``.env``.
"""

import logging
import sys

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured, MiddlewareNotUsed

logger = logging.getLogger(__name__)

# The ONLY hosts for which the bypass may boot. Anything else — a real domain, a
# public IP, or "*" — means this is not a local dev process.
LOCAL_ONLY_HOSTS = frozenset({"localhost", "127.0.0.1", "::1", "0.0.0.0", "web", "testserver"})

# Default trusted TCP peers for the per-request check. Loopback only. Widen via
# DEV_AUTH_BYPASS_TRUSTED_ADDRS only for a loopback-bound Docker publish, where
# the peer is the bridge gateway and the socket is not reachable off-host anyway.
DEFAULT_TRUSTED_ADDRS = frozenset({"127.0.0.1", "::1"})


def is_running_tests(argv=None):
    """True when executing under the Django test runner."""
    argv = sys.argv if argv is None else argv
    return "test" in argv[:3]


def dev_auth_bypass_active(debug, dev_auth_bypass, allowed_hosts):
    """Single source of truth for whether the bypass may boot.

    Returns ``False`` when the bypass is off. Raises ``ImproperlyConfigured`` —
    refusing to boot — when requested in any non-local context. Returns ``True``
    only for a strictly local dev process.
    """
    if not dev_auth_bypass:
        return False

    if not debug:
        raise ImproperlyConfigured(
            "DEV_AUTH_BYPASS=True requires DJANGO_DEBUG=True. Refusing to start — "
            "this must never run in production or SIT."
        )

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
    """Authenticate a trusted-peer request as a fixed dev user.

    Self-disables via ``MiddlewareNotUsed`` unless the startup gate agrees and we
    are not under the test runner.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        active = dev_auth_bypass_active(
            settings.DEBUG,
            getattr(settings, "DEV_AUTH_BYPASS", False),
            settings.ALLOWED_HOSTS,
        )
        if not active or is_running_tests():
            raise MiddlewareNotUsed
        self._username = getattr(settings, "DEV_AUTH_BYPASS_USER", "") or ""
        self._trusted = frozenset(
            getattr(settings, "DEV_AUTH_BYPASS_TRUSTED_ADDRS", None) or DEFAULT_TRUSTED_ADDRS
        )
        logger.warning(
            "DEV AUTH BYPASS ACTIVE — requests from %s are authenticated without a "
            "password. This must only ever run on a local dev instance.",
            sorted(self._trusted),
        )

    def __call__(self, request):
        peer = request.META.get("REMOTE_ADDR", "")
        if peer in self._trusted and not request.user.is_authenticated:
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
