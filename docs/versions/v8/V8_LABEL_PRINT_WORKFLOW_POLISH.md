# V8 Label Print Workflow Polish

Status: Complete
Last updated: 2026-06-16

## Scope

V8-007 polished product, shelf, and promotion label print workflows. It did not change label data models, template selection rules, print dimensions, or physical printer settings.

## Changes

| Area | Change | Status |
| --- | --- | --- |
| Product/shelf label setup | Added workflow warning that product/shelf labels print from active stock batches. | Current |
| Product/shelf preview | Added template type, selected batch count, copies per batch, total labels, and Open Print Dialog action. | Current |
| Promotion label setup | Added warning that promotion labels print one card per active product and require price/date review. | Current |
| Promotion preview | Added promotion, active product count, copies per product, total labels, promotion window, and Open Print Dialog action. | Current |
| Guide | Updated `docs/guides/LABEL_TEMPLATE_GUIDE.md` with V8 preview summaries. | Current |

## Rules Preserved

- Product/shelf labels still use selected active stock batches.
- Promotion labels still use active products from selected promotion scope.
- Printing still records `BARCODE_PRINT` audit entries.
- Browser/physical printer settings remain outside the app and require manual verification.

## Validation

Command:

```bash
docker compose run --rm --no-deps -v "$PWD/app:/app" web python manage.py test labels.tests --noinput --verbosity 2
```

Result: 13 tests passed.

## Notes

Physical printer checks remain required before release if any label stock or default template changes in production.
