# V9 QA Checklist

Status: Complete
Last updated: 2026-06-16

## Scope Checklist

- [x] V9 stayed within reports, audit, owner control, system visibility, and closing-process planning.
- [x] No accounting, payroll, BI warehouse, multi-store reporting, or fraud engine was added.
- [x] Sale creation logic was unchanged unless a documented report bug required it.

## Functional Checklist

- [x] Daily sales report renders and totals match approved operational definition.
- [x] Staff sales/cashier accountability report renders.
- [x] Stock, low-stock, and expiry reports render.
- [x] Promotion/below-cost reporting implementation matches scope.
- [x] Cancellation and receipt reprint tracking is visible where approved.
- [x] Audit logs are searchable/readable as scoped.
- [x] System logs and health pages remain useful.
- [x] Daily closing checklist is implemented only as a read-only operational checklist.

## Permission Checklist

- [x] Reports remain reports-capability gated.
- [x] Audit logs remain audit-capability gated.
- [x] System logs/health remain system-capability gated.
- [x] Cashier cannot see owner-only reports or audit/system pages.
- [x] Sensitive cost/profit data respects cost visibility rules.

## UI/UX Checklist

- [x] Report filters are consistent.
- [x] Empty report states are useful.
- [x] Totals and definitions are readable.
- [x] Audit log filters/search are understandable.
- [x] Owner dashboard/control pages are not visually overloaded.

## Data Safety Checklist

- [x] Reports are read-only unless a task explicitly approves otherwise.
- [x] Report queries do not mutate sales, stock, or audit data.
- [x] Cancellation/reprint tracking does not alter historical sale records incorrectly.
- [x] Backup/reset visibility does not make reset behavior easier or less safe.

## Audit/Logging Checklist

- [x] Risky actions remain traceable.
- [x] Reprint/cancellation actions remain audited.
- [x] Audit log display does not expose secrets.
- [x] System logs do not expose tokens/passwords/env secrets.

## Documentation Checklist

- [x] Approved operational report definitions documented.
- [x] Tracker and V9 task statuses updated.
- [x] Development log updated.
- [x] Release note finalized.

## Regression Checklist

- [x] Reports tests pass.
- [x] Audit tests pass if audit behavior/display changed.
- [x] Permission tests pass.
- [x] Sale cancellation/reprint tests pass if touched.

## Release Checklist

- [x] Owner-approved scope: Sidolla approved completing V7-V10 step by step; V9 report definitions are documented as operational, not accounting/tax/payroll definitions.
- [x] Tests and manual review recorded.
- [x] Approved V9 tasks complete/deferred.
- [x] Rollback notes prepared.

## Rollback Checklist

- [x] Report template/view changes can be reverted.
- [x] No data rollback required for read-only report changes.
- [x] Any new report/audit data fields have migration rollback notes if approved.

## Verification Evidence

| Check | Result |
| --- | --- |
| `docker compose run --rm --no-deps -v "$PWD/app:/app" web python manage.py check` | Passed, no issues. |
| V9 focused suite | Passed, 37 tests OK. |
| Full mounted-source Django suite | Passed, 319 tests OK. |
| `docker compose run --rm --no-deps -v "$PWD/app:/app" web python manage.py collectstatic --noinput` | Passed, 1 static file copied and assets post-processed. |
| Desktop browser smoke | Passed for Reports, Daily Closing, Daily Sales, Staff Sales, Promotion & Below-cost, Audit Logs, System Health, and Sales History. |
| Phone-width browser smoke | Passed at 390px for the same V9 pages; mobile navigation present and no page/main overflow detected. |
| Browser console | No JavaScript errors captured during V9 smoke pass. |

## Notes

- No database migrations were introduced by V9.
- V9 added read-only report/control pages only; it did not alter POS sale creation, cancellation, stock, audit writing, backup, restore, or reset behavior.
- Daily closing remains an operational checklist, not an accounting close.
