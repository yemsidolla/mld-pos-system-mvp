(function () {
    "use strict";

    var modal = document.querySelector("[data-scanner-modal]");
    if (!modal) return;

    var readerId = "melodu-scanner-reader";
    var reader = document.getElementById(readerId);
    var status = modal.querySelector("[data-scanner-status]");
    var result = modal.querySelector("[data-scanner-result]");
    var manualInput = modal.querySelector("[data-scanner-manual]");
    var fileInput = modal.querySelector("[data-scanner-file]");
    var currentTarget = null;
    var currentSelectTarget = null;
    var currentSelectMatch = "product";
    var currentContext = "general";
    var currentSubmit = false;
    var scanner = null;
    var running = false;

    function setStatus(message, tone) {
        status.textContent = message;
        status.className = "scanner-status" + (tone ? " " + tone : "");
    }

    function supportedFormats() {
        // Restrict to the codes Melodu actually uses (retail 1D + QR). Fewer
        // formats decode faster and more reliably. Falls back to "all" if the
        // enum isn't exposed.
        var F = window.Html5QrcodeSupportedFormats;
        if (!F) return undefined;
        return [
            F.QR_CODE,
            F.EAN_13,
            F.EAN_8,
            F.UPC_A,
            F.UPC_E,
            F.CODE_128,
            F.CODE_39,
            F.ITF,
        ];
    }

    function getScanner() {
        if (!window.Html5Qrcode) {
            setStatus("Scanner library is not loaded. Use manual entry.", "alert-danger");
            return null;
        }
        if (!scanner) {
            // useBarCodeDetectorIfSupported routes decoding through the device's
            // native BarcodeDetector (Android Chrome), which is much better at
            // 1D barcodes than the bundled ZXing fallback, and falls back where
            // it's unavailable (e.g. iOS Safari).
            scanner = new window.Html5Qrcode(readerId, {
                formatsToSupport: supportedFormats(),
                useBarCodeDetectorIfSupported: true,
                experimentalFeatures: { useBarCodeDetectorIfSupported: true },
                verbose: false,
            });
        }
        return scanner;
    }

    function isLocalhost() {
        return ["localhost", "127.0.0.1", "::1"].indexOf(window.location.hostname) !== -1;
    }

    function secureCameraAvailable() {
        return window.isSecureContext || isLocalhost();
    }

    function selectResolved(payload) {
        if (!currentSelectTarget || !payload) return;
        var id = null;
        if (currentSelectMatch === "stock_batch" && payload.stock_batch) {
            id = payload.stock_batch.id;
        } else if (payload.product) {
            id = payload.product.id;
        }
        if (!id) return;
        currentSelectTarget.value = String(id);
        currentSelectTarget.dispatchEvent(new Event("change", { bubbles: true }));
    }

    function fillTarget(value) {
        if (!currentTarget || !value) return;
        currentTarget.value = value;
        currentTarget.dispatchEvent(new Event("input", { bubbles: true }));
        currentTarget.dispatchEvent(new Event("change", { bubbles: true }));
        resolveCode(value).then(selectResolved).finally(function () {
            if (currentSubmit && currentTarget.form) {
                currentTarget.form.submit();
            }
        });
    }

    function closeModal() {
        stopCamera();
        modal.hidden = true;
    }

    function openModal(button) {
        var selector = button.getAttribute("data-scan-target");
        var selectSelector = button.getAttribute("data-scan-select-target");
        currentTarget = selector ? document.querySelector(selector) : null;
        currentSelectTarget = selectSelector ? document.querySelector(selectSelector) : null;
        currentSelectMatch = button.getAttribute("data-scan-select-match") || "product";
        currentContext = button.getAttribute("data-scan-context") || "general";
        currentSubmit = button.getAttribute("data-scan-submit") === "true";
        manualInput.value = currentTarget ? currentTarget.value : "";
        result.textContent = "";
        modal.hidden = false;
        setStatus("Use the camera, upload an image, or type the code manually.");
        manualInput.focus();
    }

    function stopCamera() {
        if (!scanner || !running) return Promise.resolve();
        return scanner.stop().then(function () {
            running = false;
            return scanner.clear();
        }).catch(function () {
            running = false;
        });
    }

    function onDecoded(decodedText) {
        setStatus("Code detected.");
        fillTarget(decodedText);
        closeModal();
    }

    function startCamera() {
        if (!secureCameraAvailable()) {
            setStatus("Camera scanning requires HTTPS in production. Localhost is allowed for development.", "alert-warning");
            return;
        }
        var activeScanner = getScanner();
        if (!activeScanner) return;
        stopCamera().then(function () {
            setStatus("Opening camera. Allow camera permission when asked.");
            activeScanner.start(
                { facingMode: "environment" },
                {
                    fps: 15,
                    aspectRatio: 1.777778,
                    disableFlip: false,
                    qrbox: function (viewfinderWidth, viewfinderHeight) {
                        return {
                            width: Math.min(420, Math.floor(viewfinderWidth * 0.92)),
                            height: Math.min(180, Math.floor(viewfinderHeight * 0.42)),
                        };
                    },
                    videoConstraints: {
                        facingMode: { ideal: "environment" },
                        width: { ideal: 1280 },
                        height: { ideal: 720 },
                    },
                },
                onDecoded,
                function () {}
            ).then(function () {
                running = true;
                setStatus("Camera is ready. Keep the code flat, bright, and inside the wide scan box.");
            }).catch(function (error) {
                setStatus("Camera could not start: " + (error && error.message ? error.message : error), "alert-danger");
            });
        });
    }

    function scanFile(file) {
        var activeScanner = getScanner();
        if (!activeScanner || !file) return;
        stopCamera().then(function () {
            setStatus("Reading image...");
            var scanPromise = activeScanner.scanFileV2 ? activeScanner.scanFileV2(file, true) : activeScanner.scanFile(file, true);
            scanPromise.then(function (decoded) {
                onDecoded(decoded.decodedText || decoded);
            }).catch(function () {
                setStatus("No barcode or QR code was found. Try a sharper, brighter, uncropped image with the code straight.", "alert-warning");
            }).finally(function () {
                fileInput.value = "";
            });
        });
    }

    function resolveCode(value) {
        if (!value) return Promise.resolve(null);
        var url = "/dashboard/api/scan/resolve/?value=" + encodeURIComponent(value) + "&context=" + encodeURIComponent(currentContext);
        return fetch(url, { credentials: "same-origin" })
            .then(function (response) { return response.json().then(function (payload) { return { ok: response.ok, payload: payload }; }); })
            .then(function (response) {
                if (!response.ok) {
                    result.textContent = response.payload.error || "Code could not be resolved.";
                    return null;
                }
                var payload = response.payload;
                var pieces = [payload.match_type];
                if (payload.product) pieces.push(payload.product.name + " (" + payload.product.product_code + ")");
                if (payload.stock_batch) pieces.push(payload.stock_batch.batch_no);
                result.textContent = pieces.join(" - ");
                return payload;
            })
            .catch(function () {
                result.textContent = "Code filled. Resolver was unavailable.";
                return null;
            });
    }

    document.addEventListener("click", function (event) {
        var button = event.target.closest("[data-scan-target]");
        if (button) openModal(button);
    });
    modal.querySelectorAll("[data-scanner-close]").forEach(function (button) {
        button.addEventListener("click", closeModal);
    });
    modal.querySelector("[data-scanner-start]").addEventListener("click", startCamera);
    modal.querySelector("[data-scanner-stop]").addEventListener("click", stopCamera);
    modal.querySelector("[data-scanner-apply]").addEventListener("click", function () {
        fillTarget(manualInput.value.trim());
        closeModal();
    });
    fileInput.addEventListener("change", function () {
        scanFile(fileInput.files && fileInput.files[0]);
    });
})();
