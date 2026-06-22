# V8 Barcode And QR Workflow Polish

Status: Complete
Last updated: 2026-06-16

## Scope

V8-005 polished barcode/QR scan and print guidance. Code generation, code parsing, scan resolver behavior, and stock data did not change.

## Changes

| Area | Change | Status |
| --- | --- | --- |
| Barcode/QR print setup | Added warning that Melodu custom code resolves exact batch and original barcode requires batch selection. | Current |
| Barcode/QR form | Added help text for stock batch selection and label quantity. | Current |
| Selected batch check | Added no-print confirmation panel with product, supplier, batch, expiry, original barcode, custom code, and barcode/QR image status. | Current |
| Scanner modal | Added compact scan-quality guidance for camera, upload image, and manual fallback. | Current |
| Scanner styling | Added `.scanner-help` style. | Current |

## Rules Preserved

- Custom code format remains unchanged.
- `receive_stock()` remains the source of barcode and QR generation.
- `/dashboard/api/scan/resolve/` remains read-only.
- Print audit behavior remains unchanged.

## Validation

Command:

```bash
docker compose run --rm --no-deps -v "$PWD/app:/app" web python manage.py test inventory.tests.BarcodePrintPageTests core.tests.ScannerPlacementTests core.tests.ScanResolveTests --noinput --verbosity 2
```

Result: 14 tests passed.

## Notes

Phone camera/upload decoding still depends on browser, lighting, and camera quality. No photo saving was added.
