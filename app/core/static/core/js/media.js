/* Product image field (V8 Phase 5) — preview, drag-and-drop, remove.
 *
 * Strictly additive: the <input type="file"> inside the drop zone is a real
 * working control that submits with the form on its own. Everything here is
 * enhancement, so a browser that never runs this file still uploads photos.
 *
 * Rebinds on melodu:navigated because nav.js swaps .app-frame without a page
 * load, so a form reached by an in-app click would otherwise get no handlers.
 */
(function () {
    "use strict";

    // Kept in one place so the strings are easy to translate later.
    var NOT_AN_IMAGE = "not an image";
    var DROP_UNSUPPORTED = "drag-and-drop unavailable here — tap to choose";

    function bytes(n) {
        return n < 1024 * 1024
            ? Math.round(n / 1024) + " KB"
            : (n / (1024 * 1024)).toFixed(1) + " MB";
    }

    function bind(field) {
        if (field.dataset.mediaBound === "1") return;

        var input = field.querySelector("[data-media-input]");
        var drop = field.querySelector("[data-media-drop]");
        var preview = field.querySelector("[data-media-preview]");
        var img = field.querySelector("[data-media-preview-img]");
        var empty = field.querySelector("[data-media-empty]");
        var current = field.querySelector("[data-media-current]");
        var actions = field.querySelector("[data-media-actions]");
        var nameEl = field.querySelector("[data-media-name]");
        var clear = field.querySelector("[data-media-clear]");
        if (!input || !drop || !preview || !img) return;
        field.dataset.mediaBound = "1";
        var clearBox = field.querySelector("[data-media-clear-checkbox]");

        function reject(message) {
            reset();
            if (nameEl) nameEl.textContent = message;
            if (actions) actions.classList.remove("hidden");
        }

        function show(file) {
            if (!file) return;
            if (!/^image\//.test(file.type)) {
                // accept="image/*" is only a picker hint: it is not enforced
                // for a drop, and the OS dialog lets users override it. Left
                // unchecked the form would arm with a PDF while the panel
                // still showed "Add a photo", and fail on the server.
                reject(file.name + " — " + NOT_AN_IMAGE);
                return;
            }
            // A new file supersedes a pending "delete the current image";
            // submitting both is Django's FILE_INPUT_CONTRADICTION and hard
            // fails with "submit a file or check the clear checkbox, not both".
            if (clearBox) clearBox.checked = false;
            var url = URL.createObjectURL(file);
            img.src = url;
            // Release the object URL once decoded; a till session can pick
            // through many photos and each one would otherwise be retained.
            img.onload = function () { URL.revokeObjectURL(url); };
            preview.classList.remove("hidden");
            if (empty) empty.classList.add("hidden");
            if (current) current.classList.add("hidden");
            if (actions) actions.classList.remove("hidden");
            if (nameEl) nameEl.textContent = file.name + " · " + bytes(file.size);
        }

        function reset() {
            input.value = "";
            img.removeAttribute("src");
            preview.classList.add("hidden");
            if (actions) actions.classList.add("hidden");
            if (nameEl) nameEl.textContent = "";
            if (current && !(clearBox && clearBox.checked)) current.classList.remove("hidden");
            if (empty && !current) empty.classList.remove("hidden");
        }

        input.addEventListener("change", function () {
            if (input.files && input.files[0]) show(input.files[0]);
            else reset();
        });

        if (clear) {
            clear.addEventListener("click", function (event) {
                event.preventDefault();
                event.stopPropagation();  // the wrapper is a <label>
                reset();
            });
        }

        ["dragenter", "dragover"].forEach(function (type) {
            drop.addEventListener(type, function (event) {
                event.preventDefault();
                drop.classList.add("border-primary", "bg-surface");
            });
        });
        ["dragleave", "drop"].forEach(function (type) {
            drop.addEventListener(type, function (event) {
                event.preventDefault();
                drop.classList.remove("border-primary", "bg-surface");
            });
        });
        drop.addEventListener("drop", function (event) {
            var files = event.dataTransfer && event.dataTransfer.files;
            if (!files || !files.length) return;
            var file = files[0];
            if (!/^image\//.test(file.type)) {
                reject(file.name + " — " + NOT_AN_IMAGE);
                return;
            }
            // Assign exactly ONE file. The files setter does not clamp to a
            // non-multiple input, and Django's MultiValueDict.get() returns
            // the LAST entry — so dropping three photos previewed the first
            // and saved the third, with no error anywhere.
            try {
                var dt = new DataTransfer();
                dt.items.add(file);
                input.files = dt.files;
            } catch (e) {
                // No DataTransfer/files setter: drag-and-drop cannot arm the
                // input here. Say so rather than pretending it worked.
                if (nameEl) nameEl.textContent = DROP_UNSUPPORTED;
                if (actions) actions.classList.remove("hidden");
                return;
            }
            show(file);
        });
    }

    function bindAll(root) {
        (root || document).querySelectorAll("[data-media-field]").forEach(bind);
    }

    bindAll(document);
    document.addEventListener("melodu:navigated", function () { bindAll(document); });
})();

/* Product list view toggle (V8 Phase 6) — cards vs table.
 *
 * Presentation only: both panels are already in the DOM, rendered from the
 * same queryset, so filters, sorting and pagination are untouched and there
 * is no second code path to keep in sync. The choice is per browser.
 *
 * Table is the default. Bulk work (editing many rows, comparing codes) is
 * faster in a table, so a first-time user gets the workhorse view and opts
 * into browsing, not the other way round.
 */
(function () {
    "use strict";

    var KEY = "melodu-product-view";

    function apply(root, view) {
        // The pre-paint class did its job for the first frame; from here the
        // panels are driven by `hidden` so a toggle takes effect immediately.
        document.documentElement.classList.remove("product-view-grid");
        root.querySelectorAll("[data-view-panel]").forEach(function (panel) {
            var match = panel.getAttribute("data-view-panel") === view;
            panel.classList.toggle("hidden", !match);
            // The grid needs `grid`, not the block default, when shown.
            if (panel.getAttribute("data-view-panel") === "grid") {
                panel.classList.toggle("grid", match);
            }
        });
        root.querySelectorAll("[data-view]").forEach(function (button) {
            button.setAttribute("aria-pressed", button.getAttribute("data-view") === view ? "true" : "false");
        });
    }

    function bind(root) {
        var toggle = root.querySelector("[data-view-toggle]");
        if (!toggle || toggle.dataset.viewBound === "1") return;
        toggle.dataset.viewBound = "1";

        var stored;
        try {
            stored = localStorage.getItem(KEY);
        } catch (e) { /* private mode */ }
        apply(root, stored === "grid" ? "grid" : "table");

        toggle.addEventListener("click", function (event) {
            var button = event.target.closest("[data-view]");
            if (!button) return;
            var view = button.getAttribute("data-view");
            apply(root, view);
            try {
                localStorage.setItem(KEY, view);
            } catch (e) { /* private mode */ }
        });
    }

    bind(document);
    // Same partial-navigation rebind as the media field above.
    document.addEventListener("melodu:navigated", function () { bind(document); });
})();

/* Column-filter search box -> the real search input.
 *
 * The header input deliberately has no name= (two successful controls named
 * "q" in one GET form means Django reads the LAST, which silently overrode
 * the main Search box with a stale value). It mirrors into #id_q instead, so
 * there is exactly one source of truth and the form still works with JS off
 * — the header box simply does nothing then, rather than breaking search.
 */
(function () {
    "use strict";
    document.addEventListener("input", function (event) {
        var source = event.target.closest("[data-col-filter-for]");
        if (!source) return;
        var target = document.getElementById(source.getAttribute("data-col-filter-for"));
        if (target) target.value = source.value;
    });
})();

/* A file dropped anywhere OUTSIDE the drop zone makes the browser navigate to
 * it, discarding a half-filled product form. Swallow those at document level.
 */
(function () {
    "use strict";
    ["dragover", "drop"].forEach(function (type) {
        document.addEventListener(type, function (event) {
            if (event.target.closest("[data-media-drop]")) return;
            event.preventDefault();
        });
    });
})();
