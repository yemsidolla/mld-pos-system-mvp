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

    function bytes(n) {
        return n < 1024 * 1024
            ? Math.round(n / 1024) + " KB"
            : (n / (1024 * 1024)).toFixed(1) + " MB";
    }

    function bind(field) {
        if (field.dataset.mediaBound === "1") return;
        field.dataset.mediaBound = "1";

        var input = field.querySelector("[data-media-input]");
        var drop = field.querySelector("[data-media-drop]");
        var preview = field.querySelector("[data-media-preview]");
        var img = field.querySelector("[data-media-preview-img]");
        var empty = field.querySelector("[data-media-empty]");
        var current = field.querySelector("[data-media-current]");
        var actions = field.querySelector("[data-media-actions]");
        var nameEl = field.querySelector("[data-media-name]");
        var clear = field.querySelector("[data-media-clear]");
        if (!input || !drop) return;

        function show(file) {
            if (!file || !/^image\//.test(file.type)) return;
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
            if (current) current.classList.remove("hidden");
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
            // Assigning a DataTransfer list is what makes the dropped file
            // part of the actual form submission, not just the preview.
            input.files = files;
            show(files[0]);
        });
    }

    function bindAll(root) {
        (root || document).querySelectorAll("[data-media-field]").forEach(bind);
    }

    bindAll(document);
    document.addEventListener("melodu:navigated", function () { bindAll(document); });
})();
