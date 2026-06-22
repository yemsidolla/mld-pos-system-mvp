# V8 Stock Batch Visibility Polish

Status: Complete
Last updated: 2026-06-16

## Scope

V8-002 improved stock overview and stock batch detail visibility without changing stock data, stock math, database schema, or permissions.

## Changes

| Area | Change | Status |
| --- | --- | --- |
| Stock overview batch table | Added supplier, receiver/date, expiry state, days to expiry, received/available quantities, selling price, custom code, original barcode, and print shortcut. | Current |
| Cost visibility | Actual unit cost appears only when `dashboard_can_view_costs` is true; other users see `Cost hidden`. | Current |
| Batch detail metrics | Changed available-only quantity into received/available context and expiry status badge. | Current |
| Batch detail metadata | Added batch number, original barcode, received by/at, barcode image status, and QR image status. | Current |
| Batch movement preview | Added latest five movements on batch detail and gated movement report link behind report permission. | Current |
| Styling | Added reusable `.table-actions` helper for compact table buttons. | Current |

## Files Changed

- `app/inventory/views.py`
- `app/templates/inventory/inventory_summary.html`
- `app/templates/inventory/stock_batch_detail.html`
- `app/core/context_processors.py`
- `app/core/static/core/css/dashboard.css`
- `app/inventory/tests.py`

## Validation

Command:

```bash
docker compose run --rm --no-deps -v "$PWD/app:/app" web python manage.py test inventory.tests.InventoryAdjustmentTests --noinput --verbosity 2
```

Result: 15 tests passed.

## Notes

- No stock-changing service behavior changed.
- No migration was added.
- Cost data remains hidden for users whose role is removed from Store Settings cost visibility.
- Physical stock movement drilldown remains part of the broader V8-010 traceability review.
