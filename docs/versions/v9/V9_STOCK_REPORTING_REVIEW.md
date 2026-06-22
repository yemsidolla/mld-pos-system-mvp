# V9-004 Stock, Low-stock, And Expiry Reporting Review

Status: Complete
Last updated: 2026-06-16

## Purpose

Make stock-risk reports clear enough for owner and manager action without changing inventory math.

## Definitions

| Report | Definition | Status |
| --- | --- | --- |
| Stock Summary | Active products with available stock counted from active, unexpired batches only. | Current |
| Low Stock | Products where available active, unexpired stock is at or below product minimum stock. | Current |
| Reorder Gap | `product.min_stock - available_stock`, never below zero. | Current |
| Expiry Report | Active batches with available stock that are expired or due within the warning window. | Current |
| Review Now | Expired or critical expiry batches. | Current |

## Implementation

- Updated `app/reports/views.py`.
- Updated `app/templates/reports/stock_summary.html`.
- Updated `app/templates/reports/low_stock.html`.
- Updated `app/templates/reports/expiry.html`.
- Updated `app/reports/tests.py`.

## What Changed

- Added report-definition panels to stock summary, low-stock, and expiry reports.
- Added out-of-stock and healthy product counts to stock summary.
- Added out-of-stock count to low-stock report.
- Prioritized low-stock rows by reorder gap, then product name.
- Added review-now count to expiry report.

## What Did Not Change

- No `Product`, `StockBatch`, or `InventoryMovement` behavior changed.
- No stock-in, adjustment, damage, expiry, sale, or cancellation service changed.
- No database migrations were introduced.

## Verification

```bash
docker compose run --rm --no-deps -v "$PWD/app:/app" web python manage.py test reports.tests.ReportPageTests --noinput --verbosity 1
```

Result: 13 tests OK.
