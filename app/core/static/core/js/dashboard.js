(function () {
    "use strict";

    document.querySelectorAll("[data-confirm-message]").forEach(function (element) {
        element.addEventListener("click", function (event) {
            var message = element.getAttribute("data-confirm-message");
            if (message && !window.confirm(message)) {
                event.preventDefault();
            }
        });
    });

    document.querySelectorAll("[data-table-filter]").forEach(function (input) {
        var selector = input.getAttribute("data-table-filter");
        var rows = Array.prototype.slice.call(document.querySelectorAll(selector));
        function applyFilter() {
            var query = input.value.trim().toLowerCase();
            rows.forEach(function (row) {
                var text = row.textContent.toLowerCase();
                row.hidden = query && text.indexOf(query) === -1;
            });
        }
        input.addEventListener("input", applyFilter);
        input.addEventListener("change", applyFilter);
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

    document.querySelectorAll("[data-quick-create]").forEach(function (button) {
        button.addEventListener("click", function () { openQuickCreate(button); });
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
