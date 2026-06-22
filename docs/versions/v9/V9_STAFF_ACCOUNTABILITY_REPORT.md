# V9-003 Staff Sales And Cashier Accountability Report

Status: Complete
Last updated: 2026-06-16

## Purpose

Help the owner review cashier activity without turning the POS into payroll or accounting software.

## Definition

| Signal | Definition | Status |
| --- | --- | --- |
| Completed sales | Count of sales with `status=COMPLETED` by cashier. | Current |
| Total sales | Sum of completed `Sale.final_amount` by cashier. | Current |
| Cancelled sales | Count of sales with `status=CANCELLED` by cashier; exception signal only. | Current |
| Receipt reprints | Count of `AuditLog.Action.RECEIPT_PRINT` events for sales owned by the cashier. | Current |
| Below-cost overrides | Count of completed sale items with `override_by` set. | Current |
| Discounts | Sum of completed `Sale.discount_amount` by cashier. | Current |
| Average sale | Completed total sales divided by completed sale count. | Current |
| Cost/margin | Cost and margin from sale-item snapshots, visible only when cost visibility allows it. | Current |

## Implementation

- Updated `app/reports/views.py::staff_sales_report_view`.
- Updated `app/templates/reports/staff_sales.html`.
- Updated `app/reports/tests.py`.

## What Changed

- Added report definition guidance.
- Added summary cards for cancelled sales, receipt reprints, below-cost overrides, discounts, cost of goods, and gross margin.
- Added a cashier accountability table with completed count, cancelled count, reprints, overrides, discounts, average sale, total sales, and optional cost/margin.
- Reused receipt reprint audit rows instead of adding a counter field to `Sale`.

## What Did Not Change

- No sale service logic changed.
- No receipt reprint behavior changed.
- No payroll/accounting workflow was added.
- No database migrations were introduced.

## Verification

```bash
docker compose run --rm --no-deps -v "$PWD/app:/app" web python manage.py test reports.tests.ReportPageTests --noinput --verbosity 1
```

Result: 13 tests OK.
