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

(function () {
    "use strict";

    var LABELS = {
        CASH: "Confirm Cash Payment",
        KHQR: "Customer Paid by KHQR",
        ABA: "Confirm ABA Payment",
        CARD: "Confirm Card Payment",
    };

    function dialog() { return document.querySelector("[data-payment-dialog]"); }

    document.addEventListener("click", function (event) {
        var openButton = event.target.closest("[data-open-payment]");
        if (openButton) {
            var box = dialog();
            if (box) {
                box.hidden = false;
                var cash = box.querySelector("[data-change-input]");
                if (cash) cash.focus();
            }
            return;
        }

        var closeButton = event.target.closest("[data-payment-close]");
        if (closeButton) {
            var openBox = dialog();
            if (openBox) openBox.hidden = true;
            return;
        }

        var choose = event.target.closest("[data-payment-choose]");
        if (choose) {
            var method = choose.getAttribute("data-payment-choose");
            var box2 = dialog();
            if (!box2) return;
            box2.querySelectorAll("[data-payment-choose]").forEach(function (button) {
                button.classList.toggle("active", button === choose);
            });
            box2.querySelectorAll("[data-payment-pane]").forEach(function (pane) {
                pane.hidden = pane.getAttribute("data-payment-pane") !== method;
            });
            var hiddenField = document.querySelector("[data-payment-method]");
            if (hiddenField) hiddenField.value = method;
            var label = box2.querySelector("[data-payment-confirm-label]");
            if (label && LABELS[method]) label.textContent = LABELS[method];
            if (method === "CASH") {
                var cashInput = box2.querySelector("[data-change-input]");
                if (cashInput) cashInput.focus();
            }
        }
    });

    document.addEventListener("keydown", function (event) {
        if (event.key === "Escape") {
            var box = dialog();
            if (box && !box.hidden) box.hidden = true;
        }
    });
})();
