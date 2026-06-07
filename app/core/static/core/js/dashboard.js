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
})();
