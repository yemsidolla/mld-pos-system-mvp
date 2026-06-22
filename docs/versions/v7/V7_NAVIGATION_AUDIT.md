# V7-001 Navigation And Naming Cleanup Audit

Status: Complete
Last updated: 2026-06-16

## Scope

V7-001 reviewed dashboard navigation groups, item labels, destination page titles, and role-aware visibility. This task was limited to low-risk naming cleanup and test coverage. It did not change routes, permissions, models, business logic, or the design system.

## Sources Inspected

- `app/core/context_processors.py`
- `app/templates/dashboard/base.html`
- `app/templates/dashboard/home.html`
- `app/templates/core/store_settings.html`
- `app/templates/core/auth_settings.html`
- `app/templates/core/styleguide.html`
- `app/core/tests.py`
- `app/melodu_pos/urls.py`
- `docs/DESIGN_SYSTEM.md`
- `docs/product/00_CURRENT_SYSTEM_MAP.md`
- `docs/versions/v7/V7_TASKS.md`

## Findings

| Finding | Decision | Status |
| --- | --- | --- |
| `Settings` navigation pointed to the Store & Printer Settings page. | Rename nav item to `Store Settings` for clearer destination. | Complete |
| `Login & Auth` navigation opened a page titled `Login & Authentication`. | Standardize on `Login & Authentication`. | Complete |
| `Styleguide` was less readable than normal staff-facing spacing. | Standardize visible label/title to `Style Guide` and page title to `Living Style Guide`. | Complete |
| Existing V5 navigation grouping already matches the major module structure. | Keep grouping unchanged. | Complete |
| `Receive Stock`, `Stock Overview`, `Barcode / QR Print`, `Print Labels`, `Promotion Labels`, and `Label Templates` are intentionally distinct. | Leave unchanged for V7-001; deeper label workflow consolidation belongs to V8. | Complete |

## Files Changed

- `app/core/context_processors.py`
- `app/templates/core/auth_settings.html`
- `app/templates/core/styleguide.html`
- `app/core/tests.py`
- `docs/versions/VERSION_COMPLETION_TRACKER.md`
- `docs/versions/v7/V7_TASKS.md`
- `docs/versions/v7/V7_NAVIGATION_AUDIT.md`
- `docs/DEVELOPMENT_LOG.md`

## Verification

```bash
docker compose run --rm web python manage.py check
docker compose run --rm web python manage.py test core.tests.DashboardShellTests core.tests.RoleAwareHomeTests core.tests.StyleguideAccessTests core.tests.AuthSettingsTests
```

Result:

```text
System check identified no issues.
13 tests OK.
```

Additional mounted-source regression after V7-004:

```bash
docker compose run --rm --no-deps -v "$PWD/app:/app" web python manage.py test core.tests.DashboardShellTests core.tests.RoleAwareHomeTests core.tests.StyleguideAccessTests core.tests.AuthSettingsTests pos.tests.PosPageTests pos.tests.QuickKeyTests pos.tests.PaymentFlowTests core.tests.ScanResolveTests core.tests.ScannerPlacementTests catalog.tests.ProductDashboardTests catalog.tests.ProductClassificationTests catalog.tests.ProductColumnFilterTests --noinput --verbosity 1
```

Result: 55 V7 regression tests OK.

## Completion Rule

This task is complete. Do not delete or reimplement this cleanup in future versions. If labels need further changes, create a new task and reference this audit.
