# V7-005 Inventory And Stock Receiving Workflow Polish

Status: Complete
Last updated: 2026-06-16

## Scope

V7-005 polished inventory summary, stock receiving, and batch detail pages while
keeping existing stock-in, adjustment, damage, expiry, movement, audit, and
permission behavior unchanged.

## Changes

| Change | Reason | Status |
| --- | --- | --- |
| Added practical help text to stock-in fields. | Inventory staff need to understand product barcode requirements, batch quantity, expiry, actual cost, landed cost, selling price, and receiving notes before committing stock. | Complete |
| Added `Receive Another Batch` after a successful stock-in. | Receiving often happens repeatedly; the next safe action should be one click away. | Complete |
| Clarified inventory search copy and placeholder. | The lookup accepts product names, product codes, original barcodes, batch numbers, and Melodu custom codes. | Complete |
| Added a `Level` column to product stock summary. | Low-stock products are easier to spot without changing stock calculations. | Complete |
| Added an `Open` action to each batch row. | Batch detail is the place for adjustments, damage, expiry, and label actions. | Complete |
| Added guidance and field errors to batch adjustment/damage/expiry forms. | Operators can see exactly which actions add, remove, or zero stock and why a required reason matters. | Complete |

## Files Changed

- `app/inventory/forms.py`
- `app/inventory/views.py`
- `app/templates/inventory/stock_in.html`
- `app/templates/inventory/inventory_summary.html`
- `app/templates/inventory/stock_batch_detail.html`
- `app/inventory/tests.py`
- `docs/versions/VERSION_COMPLETION_TRACKER.md`
- `docs/versions/v7/V7_TASKS.md`
- `docs/versions/v7/V7_INVENTORY_STOCK_RECEIVING_POLISH.md`
- `docs/DEVELOPMENT_LOG.md`

## Verification

Run tests against the mounted working tree because the compose `web` service
does not bind-mount source code by default.

```bash
docker compose run --rm --no-deps -v "$PWD/app:/app" web python manage.py check
docker compose run --rm --no-deps -v "$PWD/app:/app" web python manage.py test inventory --noinput --verbosity 1
docker compose run --rm --no-deps -v "$PWD/app:/app" web python manage.py test core.tests.DashboardShellTests core.tests.RoleAwareHomeTests core.tests.StyleguideAccessTests core.tests.AuthSettingsTests pos.tests.PosPageTests pos.tests.QuickKeyTests pos.tests.PaymentFlowTests core.tests.ScanResolveTests core.tests.ScannerPlacementTests catalog.tests.ProductDashboardTests catalog.tests.ProductClassificationTests catalog.tests.ProductColumnFilterTests inventory --noinput --verbosity 1
```

Result:

```text
System check identified no issues.
23 inventory tests OK.
78 mounted-source V7 regression tests OK.
```

## Completion Rule

This task is complete. Future inventory work should preserve the existing
service-backed stock-in and adjustment workflows and add new behavior through a
tracked task.
