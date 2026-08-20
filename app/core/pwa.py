"""Progressive web app plumbing: manifest, service worker, offline page.

The service worker and manifest are served from the site root rather than from
``/static/`` because a worker may only control URLs at or below its own path,
and the app needs scope over ``/``. All three views are deliberately public:
the browser fetches them before anyone has logged in.
"""

import hashlib
import json

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.templatetags.static import static
from django.urls import reverse
from django.views.decorators.http import require_http_methods

APP_NAME = "Melodu POS"
APP_SHORT_NAME = "Melodu"
THEME_COLOR = "#0b1220"       # --color-ink, the app chrome
BACKGROUND_COLOR = "#070b15"  # --color-auth-bg, what the splash shows

# Shell assets worth having on disk. Deliberately small: the fonts and styles
# that make the offline page and a cold start look right, nothing data-bearing.
PRECACHE_STATIC = (
    "core/css/cascade.css",
    "core/css/tailwind.css",
    "core/css/dashboard.css",
    "core/js/nav.js",
    "core/fonts/noto-sans-khmer.woff2",
    "core/icons/icon-192.png",
    "core/icons/icon-512.png",
)


def _precache_urls():
    return [static(path) for path in PRECACHE_STATIC]


def _version(urls):
    """Cache-busting token derived from the asset URLs themselves.

    Static files are hashed by ManifestStaticFilesStorage, so any deploy that
    changes an asset changes this token, which retires the old caches without
    anyone having to remember to bump a constant.
    """
    return hashlib.sha256("|".join(urls).encode()).hexdigest()[:12]


@require_http_methods(["GET", "HEAD"])
def manifest_view(request):
    icons = [
        {
            "src": static("core/icons/icon-192.png"),
            "sizes": "192x192",
            "type": "image/png",
            "purpose": "any",
        },
        {
            "src": static("core/icons/icon-512.png"),
            "sizes": "512x512",
            "type": "image/png",
            "purpose": "any",
        },
        {
            "src": static("core/icons/icon-maskable-512.png"),
            "sizes": "512x512",
            "type": "image/png",
            "purpose": "maskable",
        },
    ]
    payload = {
        "id": "/dashboard/",
        "name": APP_NAME,
        "short_name": APP_SHORT_NAME,
        "description": "Point of sale and inventory for the store counter.",
        "start_url": reverse("dashboard-home"),
        "scope": "/",
        "display": "standalone",
        "orientation": "any",
        "theme_color": THEME_COLOR,
        "background_color": BACKGROUND_COLOR,
        "icons": icons,
    }
    response = JsonResponse(payload, content_type="application/manifest+json")
    # Public and immutable enough to cache briefly, but not so long that a
    # rename or icon swap takes a day to reach the tills.
    response["Cache-Control"] = "public, max-age=3600"
    return response


@require_http_methods(["GET", "HEAD"])
def service_worker_view(request):
    urls = _precache_urls()
    context = {
        "version": _version(urls),
        "precache_json": json.dumps(urls),
        "offline_url": reverse("pwa-offline"),
        # Not static(""): ManifestStaticFilesStorage has no entry for an
        # empty path and would raise. The prefix is what we actually want.
        "static_prefix": settings.STATIC_URL,
    }
    response = render(
        request,
        "core/sw.js",
        context,
        content_type="text/javascript",
    )
    # Lets the worker claim the whole origin even though we could serve it
    # from anywhere, and keeps browsers from pinning a stale copy.
    response["Service-Worker-Allowed"] = "/"
    response["Cache-Control"] = "no-cache"
    return response


@require_http_methods(["GET", "HEAD"])
def offline_view(request):
    response = render(request, "core/offline.html")
    response["Cache-Control"] = "no-cache"
    return response
