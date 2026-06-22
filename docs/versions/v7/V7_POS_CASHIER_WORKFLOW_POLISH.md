# V7-003 POS Cashier Workflow Polish

Status: Complete
Last updated: 2026-06-16

## Scope

V7-003 reviewed POS cashier workflow and fixed a quick-key regression without changing sale confirmation, payment, stock deduction, permissions, or inventory logic.

## Changes

| Change | Reason | Status |
| --- | --- | --- |
| Quick-key buttons now submit `original_barcode` instead of `product_code`. | POS scan logic accepts original barcode or Melodu custom code; product-code submission made quick keys fail. | Complete |
| Hand-picked quick keys now hide products without an original barcode. | Avoids rendering unusable cashier buttons. | Complete |
| Top-seller quick keys and promotion keys now exclude products without original barcode. | Keeps generated quick keys compatible with POS scan rules. | Complete |
| Added tests for barcode-backed quick keys and hidden no-barcode quick keys. | Protects the workflow from regression. | Complete |

## Files Changed

- `app/pos/views.py`
- `app/templates/pos/pos_sale.html`
- `app/pos/tests.py`
- `docs/versions/VERSION_COMPLETION_TRACKER.md`
- `docs/versions/v7/V7_TASKS.md`
- `docs/versions/v7/V7_POS_CASHIER_WORKFLOW_POLISH.md`
- `docs/DEVELOPMENT_LOG.md`

## Verification

```bash
docker compose run --rm web python manage.py check
docker compose run --rm web python manage.py test pos.tests.PosPageTests pos.tests.QuickKeyTests pos.tests.PaymentFlowTests core.tests.ScanResolveTests core.tests.ScannerPlacementTests
docker compose run --rm web python manage.py test pos
```

Result:

```text
System check identified no issues.
22 targeted POS/scanner tests OK.
41 POS app tests OK.
```

Additional mounted-source regression after V7-004:

```bash
docker compose run --rm --no-deps -v "$PWD/app:/app" web python manage.py test core.tests.DashboardShellTests core.tests.RoleAwareHomeTests core.tests.StyleguideAccessTests core.tests.AuthSettingsTests pos.tests.PosPageTests pos.tests.QuickKeyTests pos.tests.PaymentFlowTests core.tests.ScanResolveTests core.tests.ScannerPlacementTests catalog.tests.ProductDashboardTests catalog.tests.ProductClassificationTests catalog.tests.ProductColumnFilterTests --noinput --verbosity 1
```

Result: 55 V7 regression tests OK.

## Completion Rule

This task is complete. Future POS quick-key work should preserve the rule that visible quick keys must submit a value the existing POS scan workflow accepts.
