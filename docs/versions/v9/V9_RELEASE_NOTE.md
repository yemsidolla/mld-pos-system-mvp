# V9 Release Note

Status: Complete
Last updated: 2026-06-16

## Version Summary

V9 improves owner visibility through clearer reports, audit review, exception tracking, system visibility, and a daily operational closing checklist.

## What Changed

- Added owner dashboard/reporting audit and mapped follow-up tasks.
- Improved Daily Sales with definitions, completed/cancelled split, gross/discount/net/average metrics, payment breakdown, sale-detail links, and cost/margin visibility guards.
- Improved Staff Sales into a cashier accountability report with cancellations, receipt reprints, below-cost overrides, discounts, average sale, and optional cost/margin.
- Improved stock summary, low-stock, and expiry reports with report-definition panels and additional risk metrics.
- Added Promotion & Below-cost Report using completed sale-item snapshots.
- Added sale status filter, exception summary cards, reprint count, and audit-backed Exception Tracking on Sales History/Sale Detail.
- Improved Audit Logs with broad search, object-type filter, risk-event summary, object metadata, and risk review badges.
- Improved System Health and Live Logs with overall status, disk percent/status, log line counts, and operator notes.
- Added read-only Daily Closing Checklist under Reports.
- Added backup/reset visibility on System Health with runbook paths and explicit no-dashboard-reset safety copy.

## What Did Not Change

- No accounting or tax system.
- No payroll system.
- No external BI warehouse.
- No advanced fraud engine.
- No multi-store consolidated reporting.
- No sale creation logic changes.
- No cancellation, receipt reprint, audit-writing, backup, restore, or reset behavior changes.
- No database migrations.

## Risk Level

Medium. Reports influence operations, but V9 stayed read-only and preserved existing permission/cost-visibility gates.

## Testing Notes

- Mounted-source `manage.py check` passed.
- V9 focused suite passed: 37 tests OK.
- Full mounted-source Django suite passed: 319 tests OK.
- `collectstatic --noinput` passed after CSS/template changes.
- Desktop browser smoke passed for Reports, Daily Closing, Daily Sales, Staff Sales, Promotion & Below-cost, Audit Logs, System Health, and Sales History.
- Phone-width browser smoke passed at 390px for the same V9 pages with mobile navigation present and no page/main overflow detected.
- Browser console had no JavaScript errors during the V9 smoke pass.

## Rollback Note

Read-only report/display changes can roll back by reverting the V9 code changes. No data rollback is required because V9 introduced no migrations and no data-writing behavior.

## Recommended Next Version

V10 - Multi-store / Scale-readiness Foundation.
