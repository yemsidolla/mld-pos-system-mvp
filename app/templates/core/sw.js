// Melodu POS service worker. Rendered by core.pwa.service_worker_view so the
// precache list carries the hashed asset URLs of the running build.
//
// Caching policy is deliberately conservative. A till that shows a stale price
// or a stale stock count is worse than a till that plainly says it is offline,
// so nothing data-bearing is ever served from cache: only static assets and a
// single offline page.

const VERSION = "{{ version }}";
const STATIC_CACHE = "melodu-static-" + VERSION;
const SHELL_CACHE = "melodu-shell-" + VERSION;
const OFFLINE_URL = "{{ offline_url }}";
const STATIC_PREFIX = "{{ static_prefix }}";
const PRECACHE = {{ precache_json|safe }};

self.addEventListener("install", (event) => {
    event.waitUntil((async () => {
        const shell = await caches.open(SHELL_CACHE);
        await shell.add(new Request(OFFLINE_URL, { cache: "reload" }));
        const assets = await caches.open(STATIC_CACHE);
        // Individually, so one missing asset cannot fail the whole install.
        await Promise.all(PRECACHE.map((url) => assets.add(new Request(url, { cache: "reload" })).catch(() => {})));
        await self.skipWaiting();
    })());
});

self.addEventListener("activate", (event) => {
    event.waitUntil((async () => {
        const keep = [STATIC_CACHE, SHELL_CACHE];
        for (const key of await caches.keys()) {
            if (key.startsWith("melodu-") && keep.indexOf(key) === -1) {
                await caches.delete(key);
            }
        }
        await self.clients.claim();
    })());
});

// Assets are content-hashed, so a cached copy is never wrong for its URL:
// serve it at once and refresh in the background.
async function staleWhileRevalidate(request) {
    const cache = await caches.open(STATIC_CACHE);
    const cached = await cache.match(request);
    const network = fetch(request).then((response) => {
        if (response && response.ok && response.type === "basic") {
            cache.put(request, response.clone());
        }
        return response;
    }).catch(() => undefined);
    return cached || network.then((r) => r || Response.error());
}

// Pages always come from the network. If the network is gone, say so.
async function networkOrOfflinePage(request) {
    try {
        return await fetch(request);
    } catch (err) {
        const shell = await caches.open(SHELL_CACHE);
        const offline = await shell.match(OFFLINE_URL);
        return offline || Response.error();
    }
}

self.addEventListener("fetch", (event) => {
    const request = event.request;
    if (request.method !== "GET") {
        return;
    }
    const url = new URL(request.url);
    if (url.origin !== self.location.origin) {
        return;
    }
    // Live data and the Django admin are never intercepted.
    if (url.pathname.startsWith("/admin/") || url.pathname.startsWith("/media/") || url.pathname.indexOf("/api/") !== -1) {
        return;
    }
    if (url.pathname.startsWith(STATIC_PREFIX)) {
        event.respondWith(staleWhileRevalidate(request));
        return;
    }
    if (request.mode === "navigate") {
        event.respondWith(networkOrOfflinePage(request));
    }
});

self.addEventListener("message", (event) => {
    if (event.data === "SKIP_WAITING") {
        self.skipWaiting();
    }
});
