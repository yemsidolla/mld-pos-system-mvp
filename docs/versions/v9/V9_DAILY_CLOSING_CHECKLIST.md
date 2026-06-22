# V9-009 Daily Closing Control Checklist

Status: Complete
Last updated: 2026-06-16

## Purpose

Provide an owner/manager operational closing checklist that links to existing evidence pages without adding accounting or payroll scope.

## Definition

| Area | Evidence | Status |
| --- | --- | --- |
| Sales and cash | Daily Sales report, Sales History, payment breakdown. | Current |
| Staff accountability | Staff Sales report and exception counts. | Current |
| Stock risk | Low Stock and Expiry reports. | Current |
| Promotion risk | Promotion & Below-cost report. | Current |
| System posture | System Health and Live Logs. | Current |
| Backup posture | Deployment/backup runbook confirmation. | Needs Verification |

## Implementation

- Added `reports.views.daily_closing_checklist_view`.
- Added route `dashboard/reports/daily-closing/` named `daily-closing-checklist`.
- Added `app/templates/reports/daily_closing_checklist.html`.
- Added Reports index link.
- Added shared dashboard checklist styling.
- Updated `app/reports/tests.py`.

## What Changed

- Added a read-only Daily Closing Checklist page.
- Added closing evidence links to daily sales, staff sales, promotion report, low stock, expiry, and system health.
- Clearly states that the checklist is operational control, not accounting/tax/payroll/final financial close.

## What Did Not Change

- No closing record model was added.
- No accounting workflow was added.
- No sale, stock, audit, or backup behavior changed.
- No database migrations were introduced.

## Verification

```bash
docker compose run --rm --no-deps -v "$PWD/app:/app" web python manage.py test reports.tests.ReportPageTests --noinput --verbosity 1
```

Result: 16 tests OK.
