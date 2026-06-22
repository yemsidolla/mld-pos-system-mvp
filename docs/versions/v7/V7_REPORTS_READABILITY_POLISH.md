# V7-007 Reports Page Readability Polish

Status: Complete
Last updated: 2026-06-16

## Scope

V7-007 polished report readability while preserving existing report inclusion
rules, calculations, permissions, routes, and report types.

## Changes

| Change | Reason | Status |
| --- | --- | --- |
| Added metric summaries to stock summary, low stock, expiry, stock movement, and staff sales reports. | Owners/managers can scan totals before reading tables. | Complete |
| Added lateral report/action links on sales, stock movement, and staff sales pages. | Related reports are easier to move between without returning to the index. | Complete |
| Wrapped report tables in shared horizontal table scrollers. | Dense reports stay usable on smaller screens. | Complete |
| Added low-stock/OK level badges to stock summary. | Stock exceptions are easier to see without opening the low-stock report. | Complete |
| Added expiry severity badges and batch detail links. | Expiry report rows now lead directly to batch-level action pages. | Complete |
| Added low-stock report `Open Stock` actions. | Staff can move from a report exception to inventory lookup quickly. | Complete |

## Files Changed

- `app/reports/views.py`
- `app/templates/reports/daily_sales.html`
- `app/templates/reports/stock_summary.html`
- `app/templates/reports/low_stock.html`
- `app/templates/reports/expiry.html`
- `app/templates/reports/stock_movements.html`
- `app/templates/reports/staff_sales.html`
- `app/reports/tests.py`
- `docs/versions/VERSION_COMPLETION_TRACKER.md`
- `docs/versions/v7/V7_TASKS.md`
- `docs/versions/v7/V7_REPORTS_READABILITY_POLISH.md`
- `docs/DEVELOPMENT_LOG.md`

## Verification

Run tests against the mounted working tree because the compose `web` service
does not bind-mount source code by default.

```bash
docker compose run --rm --no-deps -v "$PWD/app:/app" web python manage.py check
docker compose run --rm --no-deps -v "$PWD/app:/app" web python manage.py test reports --noinput --verbosity 1
docker compose run --rm --no-deps -v "$PWD/app:/app" web python manage.py test core.tests.DashboardShellTests core.tests.RoleAwareHomeTests core.tests.StyleguideAccessTests core.tests.AuthSettingsTests pos.tests.PosPageTests pos.tests.QuickKeyTests pos.tests.PaymentFlowTests pos.tests.PromotionDashboardTests core.tests.ScanResolveTests core.tests.ScannerPlacementTests catalog.tests.ProductDashboardTests catalog.tests.ProductClassificationTests catalog.tests.ProductColumnFilterTests inventory labels reports --noinput --verbosity 1
```

Result:

```text
System check identified no issues.
11 reports tests OK.
104 mounted-source V7 regression tests OK.
```

## Completion Rule

This task is complete. Future report calculation or export changes belong to a
tracked V9/reporting task unless explicitly scoped earlier.
