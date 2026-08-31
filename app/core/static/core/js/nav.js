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

/* Sidebar group accordion (V8).
 *
 * Lives here rather than in dashboard.js because it has to cooperate with the
 * partial navigation above: clicking a sidebar link swaps only .app-frame, so
 * the sidebar DOM is never re-rendered and a naive accordion would keep the
 * previously-active group open forever. openActiveGroup() is therefore called
 * on every navigation, not just on load.
 *
 * State is per group label in localStorage. Collapsed is the exception, not
 * the default: a group the user never touched stays open.
 */
(function () {
    "use strict";

    var KEY = "melodu-nav-collapsed";
    var sidebar = document.querySelector(".app-sidebar");
    if (!sidebar) return;

    function readCollapsed() {
        try {
            return JSON.parse(localStorage.getItem(KEY)) || {};
        } catch (e) {
            return {};
        }
    }

    function writeCollapsed(state) {
        try {
            localStorage.setItem(KEY, JSON.stringify(state));
        } catch (e) { /* private mode */ }
    }

    function applyGroup(group, collapsed) {
        group.setAttribute("data-collapsed", collapsed ? "true" : "false");
        var toggle = group.querySelector("[data-nav-group-toggle]");
        if (toggle) toggle.setAttribute("aria-expanded", collapsed ? "false" : "true");
    }

    function restore() {
        var state = readCollapsed();
        sidebar.querySelectorAll("[data-nav-group]").forEach(function (group) {
            applyGroup(group, state[group.getAttribute("data-nav-group")] === true);
        });
    }

    /* The group holding the current page must never be collapsed — otherwise
     * the active item is invisible and the user cannot see where they are. */
    function openActiveGroup() {
        var active = sidebar.querySelector(".nav-list .nav-item.active");
        if (!active) return;
        var group = active.closest("[data-nav-group]");
        if (!group || group.getAttribute("data-collapsed") !== "true") return;
        var state = readCollapsed();
        delete state[group.getAttribute("data-nav-group")];
        writeCollapsed(state);
        applyGroup(group, false);
    }

    sidebar.addEventListener("click", function (event) {
        var toggle = event.target.closest("[data-nav-group-toggle]");
        if (!toggle) return;
        var group = toggle.closest("[data-nav-group]");
        if (!group) return;
        var collapsed = group.getAttribute("data-collapsed") !== "true";
        applyGroup(group, collapsed);
        var state = readCollapsed();
        var name = group.getAttribute("data-nav-group");
        if (collapsed) state[name] = true; else delete state[name];
        writeCollapsed(state);
    });

    restore();
    openActiveGroup();
    // markActiveNav() runs on every partial navigation; re-open afterwards.
    document.addEventListener("melodu:navigated", openActiveGroup);
})();
