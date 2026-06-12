(function () {
    "use strict";

    // Event delegation throughout: bindings survive partial-navigation DOM
    // swaps without re-initialization.
    document.addEventListener("click", function (event) {
        var confirmEl = event.target.closest("[data-confirm-message]");
        if (confirmEl) {
            var message = confirmEl.getAttribute("data-confirm-message");
            if (message && !window.confirm(message)) {
                event.preventDefault();
                event.stopImmediatePropagation();
            }
        }
    }, true);

    document.addEventListener("input", function (event) {
        var input = event.target.closest("[data-table-filter]");
        if (!input) return;
        var rows = document.querySelectorAll(input.getAttribute("data-table-filter"));
        var query = input.value.trim().toLowerCase();
        rows.forEach(function (row) {
            row.hidden = query && row.textContent.toLowerCase().indexOf(query) === -1;
        });
    });

    document.addEventListener("submit", function (event) {
        var form = event.target.closest("form[data-disable-on-submit]");
        if (!form) return;
        if (form.getAttribute("data-submitting") === "true") {
            event.preventDefault();
            return;
        }

        var submitter = event.submitter;
        if (submitter && submitter.name) {
            var proxy = document.createElement("input");
            proxy.type = "hidden";
            proxy.name = submitter.name;
            proxy.value = submitter.value;
            proxy.setAttribute("data-submit-proxy", "true");
            form.appendChild(proxy);
        }

        form.setAttribute("data-submitting", "true");
        Array.prototype.forEach.call(form.querySelectorAll("button[type='submit']"), function (button) {
            var loadingText = button.getAttribute("data-loading-text");
            if (loadingText && button === submitter) button.textContent = loadingText;
            button.disabled = true;
        });
    });

    document.addEventListener("click", function (event) {
        var button = event.target.closest("[data-quantity-step]");
        if (!button) return;
        var form = button.closest("form");
        var input = form ? form.querySelector("[data-quantity-input]") : null;
        if (!input) return;

        var step = parseInt(button.getAttribute("data-quantity-step") || "0", 10);
        var current = parseInt(input.value || input.getAttribute("min") || "1", 10);
        var min = parseInt(input.getAttribute("min") || "1", 10);
        var max = parseInt(input.getAttribute("max") || "999999", 10);
        var next = Math.max(min, Math.min(max, current + step));
        input.value = String(next);
        input.dispatchEvent(new Event("change", { bubbles: true }));
        input.focus();
    });

    var quickCreateModal = document.querySelector("[data-quick-create-modal]");
    if (!quickCreateModal) return;

    var quickCreateConfig = {
        category: {
            title: "New Category",
            fields: [
                { name: "name", label: "Category name", required: true },
                { name: "description", label: "Description", type: "textarea" }
            ]
        },
        brand: {
            title: "New Brand",
            fields: [
                { name: "name", label: "Brand name", required: true },
                { name: "description", label: "Description", type: "textarea" }
            ]
        },
        supplier: {
            title: "New Supplier",
            fields: [
                { name: "name", label: "Supplier name", required: true },
                { name: "contact_person", label: "Contact person" },
                { name: "phone", label: "Phone" },
                { name: "telegram", label: "Telegram" }
            ]
        }
    };

    var quickCreateForm = quickCreateModal.querySelector("[data-quick-create-form]");
    var quickCreateFields = quickCreateModal.querySelector("[data-quick-create-fields]");
    var quickCreateTitle = quickCreateModal.querySelector("[data-quick-create-title]");
    var quickCreateStatus = quickCreateModal.querySelector("[data-quick-create-status]");
    var quickCreateErrors = quickCreateModal.querySelector("[data-quick-create-errors]");
    var quickCreateSubmit = quickCreateModal.querySelector("[data-quick-create-submit]");
    var activeQuickCreateButton = null;

    function getCookie(name) {
        var value = "; " + document.cookie;
        var parts = value.split("; " + name + "=");
        if (parts.length === 2) return parts.pop().split(";").shift();
        return "";
    }

    function clearQuickCreateErrors() {
        quickCreateErrors.textContent = "";
        quickCreateErrors.hidden = true;
    }

    function showQuickCreateErrors(errors, fallback) {
        var messages = [];
        if (errors) {
            Object.keys(errors).forEach(function (field) {
                errors[field].forEach(function (message) {
                    messages.push((field === "__all__" ? "" : field + ": ") + message);
                });
            });
        }
        quickCreateErrors.textContent = messages.join(" ") || fallback || "Could not create this item.";
        quickCreateErrors.hidden = false;
    }

    function buildQuickCreateFields(type) {
        var config = quickCreateConfig[type];
        quickCreateFields.innerHTML = "";
        config.fields.forEach(function (field) {
            var id = "quick-create-" + type + "-" + field.name;
            var wrapper = document.createElement("div");
            var label = document.createElement("label");
            var input = field.type === "textarea" ? document.createElement("textarea") : document.createElement("input");

            label.setAttribute("for", id);
            label.textContent = field.label;
            input.id = id;
            input.name = field.name;
            if (field.required) input.required = true;
            if (field.type !== "textarea") input.type = "text";
            if (field.type === "textarea") input.rows = 2;

            wrapper.appendChild(label);
            wrapper.appendChild(input);
            quickCreateFields.appendChild(wrapper);
        });
    }

    function openQuickCreate(button) {
        var type = button.getAttribute("data-quick-create-type");
        var config = quickCreateConfig[type];
        if (!config) return;

        activeQuickCreateButton = button;
        quickCreateTitle.textContent = config.title;
        quickCreateStatus.textContent = "Create the missing item without leaving this page.";
        buildQuickCreateFields(type);
        clearQuickCreateErrors();
        quickCreateModal.hidden = false;
        var firstInput = quickCreateFields.querySelector("input, textarea");
        if (firstInput) firstInput.focus();
    }

    function closeQuickCreate() {
        quickCreateModal.hidden = true;
        quickCreateForm.reset();
        clearQuickCreateErrors();
        if (activeQuickCreateButton) activeQuickCreateButton.focus();
    }

    function appendAndSelectOption(select, item) {
        var existing = Array.prototype.find.call(select.options, function (option) {
            return option.value === String(item.id);
        });
        var option = existing || document.createElement("option");
        option.value = String(item.id);
        option.textContent = item.label;
        if (!existing) select.appendChild(option);
        select.value = String(item.id);
        select.dispatchEvent(new Event("change", { bubbles: true }));
    }

    document.addEventListener("click", function (event) {
        var button = event.target.closest("[data-quick-create]");
        if (button) openQuickCreate(button);
    });

    quickCreateModal.querySelectorAll("[data-quick-create-close]").forEach(function (button) {
        button.addEventListener("click", closeQuickCreate);
    });

    document.addEventListener("keydown", function (event) {
        if (!quickCreateModal.hidden && event.key === "Escape") closeQuickCreate();
    });

    quickCreateForm.addEventListener("submit", function (event) {
        event.preventDefault();
        if (!activeQuickCreateButton) return;

        var type = activeQuickCreateButton.getAttribute("data-quick-create-type");
        var targetSelector = activeQuickCreateButton.getAttribute("data-quick-create-target");
        var select = targetSelector ? document.querySelector(targetSelector) : null;
        var url = quickCreateModal.getAttribute("data-quick-create-url");
        var data = new FormData(quickCreateForm);
        data.append("type", type);

        quickCreateSubmit.disabled = true;
        quickCreateStatus.textContent = "Creating...";
        clearQuickCreateErrors();

        fetch(url, {
            method: "POST",
            body: data,
            credentials: "same-origin",
            headers: { "X-CSRFToken": getCookie("csrftoken") }
        }).then(function (response) {
            return response.json().then(function (payload) {
                return { ok: response.ok, payload: payload };
            });
        }).then(function (response) {
            if (!response.ok) {
                showQuickCreateErrors(response.payload.errors, response.payload.error);
                quickCreateStatus.textContent = "Review the fields and try again.";
                return;
            }
            if (select) appendAndSelectOption(select, response.payload.item);
            closeQuickCreate();
        }).catch(function () {
            showQuickCreateErrors(null, "Quick add was unavailable. Try again.");
            quickCreateStatus.textContent = "Review the fields and try again.";
        }).finally(function () {
            quickCreateSubmit.disabled = false;
        });
    });
})();

(function () {
    "use strict";

    function posScanInput() {
        return document.querySelector("[data-pos-scan-form]")
            ? document.getElementById("id_scan_value")
            : null;
    }

    document.addEventListener("keydown", function (event) {
        if (event.key === "F9") {
            var shortcutButton = document.querySelector('[data-shortcut="F9"]');
            if (shortcutButton && !shortcutButton.disabled) {
                event.preventDefault();
                shortcutButton.click();
            }
        }
        if (event.key === "Escape") {
            var scanInput = posScanInput();
            if (scanInput) {
                scanInput.value = "";
                scanInput.focus();
            }
        }
    });

    document.addEventListener("input", function (event) {
        var changeInput = event.target.closest("[data-change-input]");
        if (!changeInput) return;
        var changeOutput = document.querySelector("[data-change-output]");
        var totalNode = document.querySelector("[data-cart-total]");
        if (!changeOutput || !totalNode) return;
        var total = parseFloat(totalNode.getAttribute("data-cart-total")) || 0;
        var received = parseFloat(changeInput.value);
        if (isNaN(received)) {
            changeOutput.textContent = "—";
            changeOutput.classList.remove("change-negative");
            return;
        }
        var change = received - total;
        changeOutput.textContent = change.toFixed(2);
        changeOutput.classList.toggle("change-negative", change < 0);
    });

    // Page-load effects that must re-run after a partial navigation swap.
    window.meloduPageInit = function (root) {
        root = root || document;
        var scanInput = posScanInput();
        if (scanInput) {
            scanInput.focus();
            scanInput.select();
        }
        root.querySelectorAll(".alert-success").forEach(function (alert) {
            if (alert.getAttribute("data-toast-bound")) return;
            alert.setAttribute("data-toast-bound", "1");
            window.setTimeout(function () {
                alert.classList.add("alert-fade");
                window.setTimeout(function () { alert.remove(); }, 600);
            }, 4000);
        });
    };
    window.meloduPageInit(document);
})();

(function () {
    "use strict";

    var overlay = document.getElementById("quick-find");
    if (!overlay) return;
    var input = overlay.querySelector("input");
    var results = overlay.querySelector("[data-qf-results]");
    var endpoint = overlay.getAttribute("data-endpoint");

    function open() {
        overlay.hidden = false;
        results.innerHTML = "";
        input.value = "";
        input.focus();
    }
    function close() { overlay.hidden = true; }

    document.addEventListener("keydown", function (event) {
        if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
            event.preventDefault();
            overlay.hidden ? open() : close();
        }
        if (event.key === "Escape" && !overlay.hidden) close();
    });
    overlay.addEventListener("click", function (event) {
        if (event.target === overlay) close();
    });

    function row(label, sub) {
        var div = document.createElement("div");
        div.className = "qf-row";
        var strong = document.createElement("strong");
        strong.textContent = label;
        var small = document.createElement("small");
        small.className = "mono";
        small.textContent = sub;
        div.appendChild(strong);
        div.appendChild(small);
        return div;
    }

    input.addEventListener("keydown", function (event) {
        if (event.key !== "Enter") return;
        event.preventDefault();
        var value = input.value.trim();
        if (!value) return;
        results.innerHTML = "";
        results.appendChild(row("Searching…", value));
        fetch(endpoint + "?value=" + encodeURIComponent(value) + "&context=quickfind", {
            headers: { Accept: "application/json" },
            credentials: "same-origin",
        })
            .then(function (response) { return response.json(); })
            .then(function (data) {
                results.innerHTML = "";
                if (data.status !== "ok") {
                    results.appendChild(row(data.error || "No match found.", value));
                    return;
                }
                if (data.product) {
                    results.appendChild(row(data.product.name, data.product.product_code + " · " + (data.product.original_barcode || "")));
                }
                var batches = data.stock_batches || (data.stock_batch ? [data.stock_batch] : []);
                batches.forEach(function (batch) {
                    results.appendChild(
                        row("Batch " + batch.batch_no, "exp " + batch.expiry_date + " · " + batch.quantity_available + " avail · " + batch.selling_price)
                    );
                });
                (data.warnings || []).forEach(function (warning) {
                    results.appendChild(row("⚠ " + warning, ""));
                });
            })
            .catch(function () {
                results.innerHTML = "";
                results.appendChild(row("Lookup failed. Try again.", value));
            });
    });
})();
