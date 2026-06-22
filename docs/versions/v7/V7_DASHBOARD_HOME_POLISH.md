# V7-002 Dashboard Home Polish

Status: Complete
Last updated: 2026-06-16

## Scope

V7-002 polished the dashboard home page while keeping existing roles, routes, services, and data behavior unchanged.

## Changes

| Change | Reason | Status |
| --- | --- | --- |
| Renamed the POS quick action from `POS Sale` to `Open POS`. | Match the header action and reduce duplicate naming. | Complete |
| Added `Print Labels` as an inventory quick action. | Inventory staff frequently move from stock review/receiving to labels. | Complete |
| Added `Batch Upload` as a catalog quick action. | Catalog managers already have access and recent uploads are shown on the home page. | Complete |
| Added/updated role tests for inventory and cashier home behavior. | Keep shortcuts role-safe. | Complete |

## Files Changed

- `app/templates/dashboard/home.html`
- `app/core/tests.py`
- `docs/versions/VERSION_COMPLETION_TRACKER.md`
- `docs/versions/v7/V7_TASKS.md`
- `docs/versions/v7/V7_DASHBOARD_HOME_POLISH.md`
- `docs/DEVELOPMENT_LOG.md`

## Verification

```bash
docker compose run --rm web python manage.py check
docker compose run --rm web python manage.py test core.tests.DashboardShellTests core.tests.RoleAwareHomeTests
```

Result:

```text
System check identified no issues.
8 tests OK.
```

Additional mounted-source regression after V7-004:

```bash
docker compose run --rm --no-deps -v "$PWD/app:/app" web python manage.py test core.tests.DashboardShellTests core.tests.RoleAwareHomeTests core.tests.StyleguideAccessTests core.tests.AuthSettingsTests pos.tests.PosPageTests pos.tests.QuickKeyTests pos.tests.PaymentFlowTests core.tests.ScanResolveTests core.tests.ScannerPlacementTests catalog.tests.ProductDashboardTests catalog.tests.ProductClassificationTests catalog.tests.ProductColumnFilterTests --noinput --verbosity 1
```

Result: 55 V7 regression tests OK.

## Completion Rule

This task is complete. Do not remove the new role-safe shortcuts unless a later dashboard-home task explicitly replaces them.
