/* POS no-reload cart (V8): scan/add/update/remove/clear post via fetch and
 * swap the main content region, so the register never flashes mid-sale.
 * Forms marked data-full-submit (checkout) keep the normal full request. */
(function () {
    "use strict";

    document.addEventListener("submit", function (event) {
        var form = event.target.closest(".pos-layout form, form[data-pos-scan]");
        if (!form || form.hasAttribute("data-full-submit")) return;
        var main = document.getElementById("main-content");
        if (!main || !window.fetch || !window.DOMParser) return;

        event.preventDefault();

        var data = new FormData(form);
        if (event.submitter && event.submitter.name) {
            data.append(event.submitter.name, event.submitter.value);
        }

        main.classList.add("frame-loading");
        fetch(form.getAttribute("action") || window.location.href, {
            method: "POST",
            body: data,
            credentials: "same-origin",
            headers: { "X-Melodu-Partial": "1" },
        })
            .then(function (response) {
                if (response.redirected && response.url.indexOf("/login") !== -1) {
                    window.location.href = response.url;
                    return null;
                }
                return response.text();
            })
            .then(function (text) {
                if (text === null) return;
                var parsed = new DOMParser().parseFromString(text, "text/html");
                var newMain = parsed.getElementById("main-content");
                if (!newMain) {
                    window.location.reload();
                    return;
                }
                main.innerHTML = newMain.innerHTML;
                if (window.meloduPageInit) window.meloduPageInit(main);
                document.dispatchEvent(new CustomEvent("melodu:pos-updated"));
            })
            .catch(function () {
                window.location.reload();
            })
            .finally(function () {
                main.classList.remove("frame-loading");
            });
    });
})();
