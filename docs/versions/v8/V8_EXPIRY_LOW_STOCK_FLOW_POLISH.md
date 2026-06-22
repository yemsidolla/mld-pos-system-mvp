# V8 Expiry And Low-Stock Flow Polish

Status: Complete
Last updated: 2026-06-16

## Scope

V8-003 improved low-stock and expiry operational visibility across stock overview and inventory reports. No threshold, stock math, model, or migration behavior changed.

## Changes

| Area | Change | Status |
| --- | --- | --- |
| Stock overview product summary | Added reorder gap, state badge, Receive Stock action, and report-gated Review Expiry action. | Current |
| Stock summary report | Added reorder units metric, reorder gap column, state badge, and Open Stock action. | Current |
| Low stock report | Added reorder units metric, reorder gap column, state badge, and Receive Stock action. | Current |
| Expiry report | Added supplier, product code, days-to-expiry, recommended next action, and Open Batch action. | Current |
| Permissions | Report shortcuts are hidden on inventory pages when the user cannot view reports. | Current |

## Rules Preserved

- Product `min_stock` remains the low-stock threshold.
- Expiry state remains `Expired`, `Critical` up to 30 days, `Warning` up to 60 days, then `Normal`.
- Sellable report stock still excludes inactive products, non-active batches, and expired batches.
- No stock-changing service behavior changed.

## Validation

Command:

```bash
docker compose run --rm --no-deps -v "$PWD/app:/app" web python manage.py test inventory.tests.InventoryAdjustmentTests reports.tests.ReportPageTests --noinput --verbosity 2
```

Result: 26 tests passed.

## Notes

Physical shelf review and purchasing decisions remain human operational steps. V8 only improves visibility and navigation.
