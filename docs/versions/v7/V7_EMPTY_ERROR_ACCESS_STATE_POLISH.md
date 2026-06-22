# V7-009 Empty, Error, and Access-State Polish

Status: Complete
Last updated: 2026-06-16

## Scope

V7-009 improved user-facing empty states and dashboard error/access pages while
preserving existing routes, permission checks, audit logging, and exception
handling.

## Changes

| Change | Reason | Status |
| --- | --- | --- |
| Added status-specific next-step guidance to dashboard 403, 404, and 500 pages. | Staff get a safe action path without seeing internal error details. | Complete |
| Removed the always-on `EVENT LOGGED` footer from non-permission error states. | Avoids implying every 404/500 is an audit event. | Complete |
| Kept 403 access-denied pages tied to `AUDIT TRAIL ACTIVE`. | Permission-denied events remain clear and traceable. | Complete |
| Added a styled `What to do next` section to the shared error page. | Error pages are more helpful without exposing technical data. | Complete |
| Improved empty states for Batch Upload recent jobs, Sales History, User Management, and Label Templates. | Common no-data pages now explain the next safe workflow step. | Complete |

## Files Changed

- `app/core/views.py`
- `app/core/permissions.py`
- `app/templates/dashboard/error.html`
- `app/core/static/core/css/dashboard.css`
- `app/templates/batch_upload/index.html`
- `app/templates/pos/sales_history.html`
- `app/templates/accounts/user_list.html`
- `app/templates/labels/template_list.html`
- `app/core/tests.py`
- `app/batch_upload/tests.py`
- `app/pos/tests.py`
- `app/labels/tests.py`
- `docs/versions/VERSION_COMPLETION_TRACKER.md`
- `docs/versions/v7/V7_TASKS.md`
- `docs/versions/v7/V7_EMPTY_ERROR_ACCESS_STATE_POLISH.md`
- `docs/DEVELOPMENT_LOG.md`

## Verification

Run tests against the mounted working tree because the compose `web` service
does not bind-mount source code by default.

```bash
docker compose run --rm --no-deps -v "$PWD/app:/app" web python manage.py check
docker compose run --rm --no-deps -v "$PWD/app:/app" web python manage.py test core.tests.DashboardErrorPageTests batch_upload.tests.BatchUploadViewTests pos.tests.SalesCancellationTests labels.tests.LabelTemplateAccessTests --noinput --verbosity 1
docker compose run --rm --no-deps -v "$PWD/app:/app" web python manage.py test core.tests.DashboardShellTests core.tests.RoleAwareHomeTests core.tests.DashboardErrorPageTests core.tests.StyleguideAccessTests core.tests.AuthSettingsTests pos.tests.PosPageTests pos.tests.QuickKeyTests pos.tests.PaymentFlowTests pos.tests.PromotionDashboardTests pos.tests.SalesCancellationTests core.tests.ScanResolveTests core.tests.ScannerPlacementTests catalog.tests.ProductDashboardTests catalog.tests.ProductClassificationTests catalog.tests.ProductColumnFilterTests inventory labels reports audit system_logs batch_upload.tests.BatchUploadViewTests accounts.tests.UserManagementTests --noinput --verbosity 1
```

Result:

```text
System check identified no issues.
16 focused empty/error/access-state tests OK.
139 mounted-source V7 regression tests OK.
```

## Completion Rule

This task is complete. Future changes to specific empty states or operator error
runbooks should be tracked under the relevant module task or V9/V10 operations
task instead of reopening V7-009.
