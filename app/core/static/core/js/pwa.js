// Registers the service worker that makes Melodu POS installable.
// Registration is best-effort: the app is fully functional without it, so a
// failure here is logged and otherwise ignored.
(function () {
    "use strict";

    if (!("serviceWorker" in navigator)) {
        return;
    }
    // Service workers require a secure context. Behind Cloudflare and nginx
    // that is always true in practice, but plain-HTTP LAN access is not.
    if (!window.isSecureContext) {
        return;
    }

    window.addEventListener("load", function () {
        navigator.serviceWorker.register("/sw.js", { scope: "/" }).then(function (registration) {
            // A new build is picked up on the next navigation rather than
            // swapped in mid-sale.
            registration.addEventListener("updatefound", function () {
                var incoming = registration.installing;
                if (!incoming) {
                    return;
                }
                incoming.addEventListener("statechange", function () {
                    if (incoming.state === "installed" && navigator.serviceWorker.controller) {
                        incoming.postMessage("SKIP_WAITING");
                    }
                });
            });
        }).catch(function (err) {
            console.warn("[melodu] service worker registration failed:", err);
        });
    });
})();
