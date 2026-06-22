# V9-006 Sale Cancellation And Receipt Reprint Tracking

Status: Complete
Last updated: 2026-06-16

## Purpose

Make sale exceptions easier for owner/manager review without changing cancellation or reprint behavior.

## Definitions

| Signal | Definition | Status |
| --- | --- | --- |
| Cancelled sale | `Sale.status=CANCELLED`; revenue exception, not completed revenue. | Current |
| Cancel reason | `Sale.cancel_reason`, required by the cancellation service/form. | Current |
| Receipt reprint | `AuditLog.Action.RECEIPT_PRINT` with `object_type=Sale` and matching sale id. | Current |
| Sale exception detail | Cancellation and reprint audit rows shown on sale detail. | Current |

## Implementation

- Added `status` filter to `pos.forms.SaleFilterForm`.
- Updated `pos.views.sales_history_view`.
- Updated `pos.views.sale_detail_view`.
- Updated `app/templates/pos/sales_history.html`.
- Updated `app/templates/pos/sale_detail.html`.
- Updated `app/pos/tests.py`.

## What Changed

- Sales History now has completed, cancelled, reprint, and completed-revenue summary cards.
- Sales History can filter by sale status.
- Sale Detail now shows receipt reprint count and an Exception Tracking table for cancellation/reprint audit rows.

## What Did Not Change

- No sale cancellation service behavior changed.
- No receipt print/reprint behavior changed.
- No audit creation behavior changed.
- No database migrations were introduced.

## Verification

```bash
docker compose run --rm --no-deps -v "$PWD/app:/app" web python manage.py test pos.tests.SalesCancellationTests pos.tests.ReceiptTests --noinput --verbosity 1
```

Result: 10 tests OK.
