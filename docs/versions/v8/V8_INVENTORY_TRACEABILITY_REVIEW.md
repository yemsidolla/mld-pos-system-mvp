# V8 Inventory Traceability Review

Status: Complete
Last updated: 2026-06-16

## Scope

V8-010 reviewed and improved dashboard traceability for stock movements and audit visibility. No movement model, audit model, or stock-changing service behavior changed.

## Changes

| Area | Change | Status |
| --- | --- | --- |
| Batch detail | Shows latest five stock movements for the batch. | Current |
| Movement report | Added search by product, batch, custom code, reference, note, or user. | Current |
| Movement report | Added movement type filter. | Current |
| Movement table | Added batch custom code, movement note, product code, and gated batch detail links. | Current |
| Audit shortcut | Added Inventory Audit Logs shortcut when the user can view audit logs. | Current |
| Permission safety | Added shared dashboard flags for inventory/audit shortcuts so report-only users do not see links they cannot open. | Current |

## Trace Paths

| Workflow | Movement | Audit | Status |
| --- | --- | --- | --- |
| Stock-in | `STOCK_IN` movement from `receive_stock()` | `STOCK_IN`, cost snapshot audit | Current |
| Sale | `SALE` movement from `confirm_sale()` | `SALE_CREATE`, below-cost/promotion audits where applicable | Current |
| Cancellation | `RETURN` movement from `cancel_sale()` | `SALE_CANCEL` | Current |
| Adjustment | `ADJUSTMENT` movement from `adjust_stock()` | `STOCK_ADJUSTMENT` | Current |
| Damage | `DAMAGE` movement from `mark_batch_damaged()` | `STOCK_ADJUSTMENT` | Current |
| Expiry | `EXPIRED` movement from `mark_batch_expired()` | `STOCK_ADJUSTMENT` | Current |

## Validation

Command:

```bash
docker compose run --rm --no-deps -v "$PWD/app:/app" web python manage.py test reports.tests.ReportPageTests audit.tests.AuditLogDashboardTests --noinput --verbosity 2
```

Result: 15 tests passed.

## Notes

There is no direct foreign key from movement to audit log in V8. Traceability is by batch, product, reference, user, timestamp, and audit module/object fields.
