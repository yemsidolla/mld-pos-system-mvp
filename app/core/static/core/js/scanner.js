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
    var captureButton = modal.querySelector("[data-scanner-capture]");
    var currentTarget = null;
    var currentSelectTarget = null;
    var currentSelectMatch = "product";
    var currentContext = "general";
    var currentSubmit = false;
    var scanner = null;
    var running = false;
    var nativeDetector = null;

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

    function nativeBarcodeFormats() {
        return ["qr_code", "ean_13", "ean_8", "upc_a", "upc_e", "code_128", "code_39", "itf"];
    }

    function getNativeDetector() {
        if (!("BarcodeDetector" in window)) return null;
        if (nativeDetector === false) return null;
        if (!nativeDetector) {
            try {
                nativeDetector = new window.BarcodeDetector({ formats: nativeBarcodeFormats() });
            } catch (error) {
                nativeDetector = false;
                return null;
            }
        }
        return nativeDetector;
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

    function getCookie(name) {
        var value = "; " + document.cookie;
        var parts = value.split("; " + name + "=");
        if (parts.length === 2) return decodeURIComponent(parts.pop().split(";").shift());
        return "";
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

    function scannerConfig() {
        return {
            fps: 12,
            disableFlip: false,
            qrbox: function (viewfinderWidth, viewfinderHeight) {
                return {
                    width: Math.min(520, Math.floor(viewfinderWidth * 0.94)),
                    height: Math.min(360, Math.floor(viewfinderHeight * 0.72)),
                };
            },
        };
    }

    function startScanner(activeScanner, cameraConfig) {
        return activeScanner.start(
            cameraConfig,
            scannerConfig(),
            onDecoded,
            function () {}
        );
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
            startScanner(activeScanner, { facingMode: { exact: "environment" } }).catch(function () {
                return startScanner(activeScanner, { facingMode: { exact: "user" } });
            }).then(function () {
                running = true;
                setStatus("Camera is ready. Keep the code flat, bright, and fully inside the scan box.");
            }).catch(function (error) {
                setStatus("Camera could not start: " + (error && error.message ? error.message : error), "alert-danger");
            });
        });
    }

    function scanFileWithHtml5(activeScanner, file) {
        var scanPromise = activeScanner.scanFileV2 ? activeScanner.scanFileV2(file, true) : activeScanner.scanFile(file, true);
        return scanPromise.then(function (decoded) {
            return decoded.decodedText || decoded;
        });
    }

    function scanFileWithServer(file) {
        var formData = new FormData();
        formData.append("image", file, file.name || "scan-image.jpg");
        return fetch("/dashboard/api/scan/decode-image/", {
            method: "POST",
            credentials: "same-origin",
            headers: { "X-CSRFToken": getCookie("csrftoken") },
            body: formData,
        }).then(function (response) {
            return response.json().then(function (payload) {
                if (!response.ok) {
                    throw new Error(payload.error || "Server could not decode the image.");
                }
                return payload.code;
            });
        });
    }

    function scanFileWithNativeDetector(file) {
        var detector = getNativeDetector();
        if (!detector || !window.createImageBitmap) return Promise.reject(new Error("Native barcode detector unavailable."));
        return window.createImageBitmap(file).then(function (bitmap) {
            return detector.detect(bitmap).then(function (codes) {
                if (bitmap.close) bitmap.close();
                if (!codes || !codes.length || !codes[0].rawValue) {
                    throw new Error("Native barcode detector found no code.");
                }
                return codes[0].rawValue;
            }).catch(function (error) {
                if (bitmap.close) bitmap.close();
                throw error;
            });
        });
    }

    function normalizeImageFile(file, maxDimension) {
        return new Promise(function (resolve, reject) {
            var reader = new FileReader();
            reader.onload = function () {
                var image = new Image();
                image.onload = function () {
                    var scale = Math.min(1, maxDimension / Math.max(image.width, image.height));
                    var width = Math.max(1, Math.round(image.width * scale));
                    var height = Math.max(1, Math.round(image.height * scale));
                    var canvas = document.createElement("canvas");
                    var context = canvas.getContext("2d");
                    canvas.width = width;
                    canvas.height = height;
                    context.fillStyle = "#ffffff";
                    context.fillRect(0, 0, width, height);
                    context.drawImage(image, 0, 0, width, height);
                    canvas.toBlob(function (blob) {
                        if (!blob) {
                            reject(new Error("Could not prepare image for scanning."));
                            return;
                        }
                        try {
                            resolve(new File([blob], "melodu-scan.jpg", { type: "image/jpeg" }));
                        } catch (error) {
                            blob.name = "melodu-scan.jpg";
                            resolve(blob);
                        }
                    }, "image/jpeg", 0.95);
                };
                image.onerror = function () { reject(new Error("Could not read that image.")); };
                image.src = reader.result;
            };
            reader.onerror = function () { reject(new Error("Could not read that image.")); };
            reader.readAsDataURL(file);
        });
    }

    function firstSuccessfulScan(scanFns) {
        return scanFns.reduce(function (promise, scanFn) {
            return promise.catch(scanFn);
        }, Promise.reject(new Error("No scan attempted.")));
    }

    function scanFile(file) {
        var activeScanner = getScanner();
        if (!activeScanner || !file) return;
        stopCamera().then(function () {
            setStatus("Reading image. Large phone photos may take a few seconds...");
            firstSuccessfulScan([
                function () { return scanFileWithNativeDetector(file); },
                function () { return scanFileWithHtml5(activeScanner, file); },
                function () { return scanFileWithServer(file); },
                function () {
                    return normalizeImageFile(file, 1800).then(function (normalizedFile) {
                        return scanFileWithHtml5(activeScanner, normalizedFile);
                    });
                },
                function () {
                    return normalizeImageFile(file, 1800).then(scanFileWithServer);
                },
                function () {
                    return normalizeImageFile(file, 2600).then(function (normalizedFile) {
                        return scanFileWithHtml5(activeScanner, normalizedFile);
                    });
                },
                function () {
                    return normalizeImageFile(file, 2600).then(scanFileWithServer);
                },
            ]).then(function (decodedText) {
                onDecoded(decodedText);
            }).catch(function () {
                setStatus("No barcode or QR code was found. On phone, use a close, bright photo where the full code is straight and fills most of the image.", "alert-warning");
            }).finally(function () {
                fileInput.value = "";
            });
        });
    }

    function captureCameraFrame() {
        var video = reader ? reader.querySelector("video") : null;
        if (!video || !video.videoWidth || !video.videoHeight) {
            setStatus("Open the camera first, then capture the frame.", "alert-warning");
            return;
        }
        var canvas = document.createElement("canvas");
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        canvas.getContext("2d").drawImage(video, 0, 0, canvas.width, canvas.height);
        setStatus("Sending camera frame to server decoder...");
        canvas.toBlob(function (blob) {
            if (!blob) {
                setStatus("Could not capture a camera frame. Try upload or manual entry.", "alert-warning");
                return;
            }
            try {
                blob.name = "camera-frame.jpg";
            } catch (error) {}
            firstSuccessfulScan([
                function () { return scanFileWithNativeDetector(blob); },
                function () { return scanFileWithServer(blob); },
                function () {
                    return normalizeImageFile(blob, 1800).then(scanFileWithServer);
                },
            ]).then(function (decodedText) {
                onDecoded(decodedText);
            }).catch(function () {
                setStatus("The captured frame could not be decoded. Move closer, improve light, and keep the full code in view.", "alert-warning");
            });
        }, "image/jpeg", 0.95);
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
    if (captureButton) captureButton.addEventListener("click", captureCameraFrame);
    modal.querySelector("[data-scanner-apply]").addEventListener("click", function () {
        fillTarget(manualInput.value.trim());
        closeModal();
    });
    fileInput.addEventListener("change", function () {
        scanFile(fileInput.files && fileInput.files[0]);
    });
})();
