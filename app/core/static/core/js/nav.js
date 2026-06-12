/* Partial navigation (V8): sidebar links swap only the page frame so the
 * sidebar never reloads. No dependency — fetch + DOMParser + History API.
 * Opt out per link with data-full-nav (print views, downloads, /admin/). */
(function () {
    "use strict";

    var frame = document.querySelector(".app-frame");
    if (!frame || !window.history || !window.fetch || !window.DOMParser) return;

    var navigating = false;

    function isInternalNavLink(link) {
        if (!link || link.hasAttribute("data-full-nav") || link.target === "_blank") return false;
        if (!link.href || link.getAttribute("href").indexOf("#") === 0) return false;
        var url = new URL(link.href, window.location.href);
        if (url.origin !== window.location.origin) return false;
        if (url.pathname.indexOf("/dashboard/") !== 0) return false;
        if (/\/(receipt|reprint|print)\//.test(url.pathname)) return false;
        return true;
    }

    function markActiveNav(pathname) {
        document.querySelectorAll(".app-sidebar .nav-item, .mobile-nav a").forEach(function (item) {
            var href = item.getAttribute("href");
            item.classList.toggle("active", href === pathname);
        });
    }

    function swapFrom(htmlText, url, push) {
        var parsed = new DOMParser().parseFromString(htmlText, "text/html");
        var newFrame = parsed.querySelector(".app-frame");
        if (!newFrame) {
            window.location.href = url;
            return;
        }
        frame.innerHTML = newFrame.innerHTML;
        document.title = parsed.title;
        if (push) window.history.pushState({ melodu: true }, "", url);
        markActiveNav(new URL(url, window.location.href).pathname);
        window.scrollTo(0, 0);
        if (window.meloduPageInit) window.meloduPageInit(frame);
        document.dispatchEvent(new CustomEvent("melodu:navigated", { detail: { url: url } }));
    }

    function navigate(url, push) {
        if (navigating) return;
        navigating = true;
        frame.classList.add("frame-loading");
        fetch(url, { credentials: "same-origin", headers: { "X-Melodu-Partial": "1" } })
            .then(function (response) {
                if (!response.ok && response.status !== 403 && response.status !== 404) {
                    throw new Error("nav " + response.status);
                }
                if (response.redirected && response.url.indexOf("/login") !== -1) {
                    window.location.href = response.url;
                    return null;
                }
                return response.text().then(function (text) {
                    swapFrom(text, response.url || url, push);
                });
            })
            .catch(function () {
                window.location.href = url;
            })
            .finally(function () {
                navigating = false;
                frame.classList.remove("frame-loading");
            });
    }

    document.addEventListener("click", function (event) {
        if (event.defaultPrevented || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
        var link = event.target.closest(".app-sidebar a, .mobile-nav a");
        if (!link || !isInternalNavLink(link)) return;
        event.preventDefault();
        navigate(link.href, true);
    });

    window.addEventListener("popstate", function () {
        navigate(window.location.href, false);
    });
})();
