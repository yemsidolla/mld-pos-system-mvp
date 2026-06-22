# V7-008 Audit, Log, and System Page Polish

Status: Complete
Last updated: 2026-06-16

## Scope

V7-008 polished support/operator pages while preserving existing permissions,
routes, audit behavior, log redaction behavior, and system checks.

## Changes

| Change | Reason | Status |
| --- | --- | --- |
| Added audit log metric cards for entry count, read-only mode, and newest-first order. | Managers can understand the audit page purpose before reading rows. | Complete |
| Added human-readable disk values to the system health view. | Raw byte counts were hard to read during operations. | Complete |
| Added system health metric cards for database, log writability, disk free space, and app version. | Operators can scan critical checks before reading the detail table. | Complete |
| Added success/danger badges for database and log writable status. | Warning states are clearer without changing the checks themselves. | Complete |
| Split live logs into guidance, errors, and application panels. | Error review is easier and the page aligns with the shared dashboard shell. | Complete |
| Added explicit live-log safety copy for redaction and 5-second auto-refresh. | Operators understand the page behavior and secret-handling boundary. | Complete |

## Files Changed

- `app/system_logs/views.py`
- `app/templates/system_logs/system_health.html`
- `app/templates/system_logs/live_logs.html`
- `app/system_logs/tests.py`
- `app/templates/audit/audit_log_list.html`
- `app/audit/tests.py`
- `docs/versions/VERSION_COMPLETION_TRACKER.md`
- `docs/versions/v7/V7_TASKS.md`
- `docs/versions/v7/V7_AUDIT_LOG_SYSTEM_PAGE_POLISH.md`
- `docs/DEVELOPMENT_LOG.md`

## Verification

Run tests against the mounted working tree because the compose `web` service
does not bind-mount source code by default.

```bash
docker compose run --rm --no-deps -v "$PWD/app:/app" web python manage.py check
docker compose run --rm --no-deps -v "$PWD/app:/app" web python manage.py test audit system_logs --noinput --verbosity 1
docker compose run --rm --no-deps -v "$PWD/app:/app" web python manage.py test core.tests.DashboardShellTests core.tests.RoleAwareHomeTests core.tests.StyleguideAccessTests core.tests.AuthSettingsTests pos.tests.PosPageTests pos.tests.QuickKeyTests pos.tests.PaymentFlowTests pos.tests.PromotionDashboardTests core.tests.ScanResolveTests core.tests.ScannerPlacementTests catalog.tests.ProductDashboardTests catalog.tests.ProductClassificationTests catalog.tests.ProductColumnFilterTests inventory labels reports audit system_logs --noinput --verbosity 1
```

Result:

```text
System check identified no issues.
15 audit/system log tests OK.
119 mounted-source V7 regression tests OK.
```

## Completion Rule

This task is complete. Future audit reporting, log export, monitoring, backup
visibility, or owner-control changes belong to tracked V9/V10 tasks unless
explicitly scoped earlier.
