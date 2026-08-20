"""Install metadata: manifest, service worker and offline page.

All three must be reachable by a browser that has not logged in, and the
worker must be served from the root so it can take scope over the whole app.
"""
import json

from django.test import TestCase
from django.urls import reverse


class PwaEndpointTests(TestCase):
    def test_manifest_is_public_and_describes_the_app(self):
        response = self.client.get(reverse("pwa-manifest"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/manifest+json")
        payload = json.loads(response.content)
        self.assertEqual(payload["name"], "Melodu POS")
        self.assertEqual(payload["display"], "standalone")
        self.assertEqual(payload["scope"], "/")
        self.assertEqual(payload["start_url"], reverse("dashboard-home"))

    def test_manifest_offers_an_installable_icon_set(self):
        payload = json.loads(self.client.get(reverse("pwa-manifest")).content)
        sizes = {icon["sizes"] for icon in payload["icons"]}
        # Chrome will not offer installation without a 192 and a 512.
        self.assertIn("192x192", sizes)
        self.assertIn("512x512", sizes)
        purposes = {icon["purpose"] for icon in payload["icons"]}
        self.assertIn("maskable", purposes)

    def test_service_worker_is_served_at_the_root_with_root_scope(self):
        url = reverse("pwa-service-worker")
        self.assertEqual(url, "/sw.js")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("javascript", response["Content-Type"])
        self.assertEqual(response["Service-Worker-Allowed"], "/")

    def test_service_worker_precaches_real_asset_urls(self):
        body = self.client.get(reverse("pwa-service-worker")).content.decode()
        self.assertIn("const PRECACHE = [", body)
        self.assertIn("tailwind", body)
        # The offline page must be a URL the worker can actually fetch.
        self.assertIn(reverse("pwa-offline"), body)

    def test_service_worker_version_tracks_the_assets(self):
        from core import pwa

        first = pwa._version(["/static/a.css"])
        self.assertNotEqual(first, pwa._version(["/static/a.f00ba7.css"]))
        self.assertEqual(first, pwa._version(["/static/a.css"]))

    def test_endpoints_answer_head_requests(self):
        # Proxies and link checkers send HEAD; require_GET alone would 405.
        for name in ("pwa-manifest", "pwa-service-worker", "pwa-offline"):
            with self.subTest(name=name):
                self.assertEqual(self.client.head(reverse(name)).status_code, 200)

    def test_offline_page_is_public(self):
        response = self.client.get(reverse("pwa-offline"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No connection")

    def test_login_page_advertises_the_manifest(self):
        response = self.client.get(reverse("dashboard-login"))
        self.assertContains(response, 'rel="manifest"')
        self.assertContains(response, 'name="theme-color"')
        # The registration script is hashed by ManifestStaticFilesStorage, so
        # match the stem rather than a literal filename.
        self.assertContains(response, "core/js/pwa")
