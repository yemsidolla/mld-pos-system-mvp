# V7-010 Mobile and Tablet Usability Pass

Status: Complete
Last updated: 2026-06-16

## Scope

V7-010 improved responsive behavior for the Django-template dashboard shell and
core staff workflows. It preserved existing business logic, routes, permissions,
scanner behavior, and POS sale behavior.

## Changes

| Change | Reason | Status |
| --- | --- | --- |
| Added responsive guards for topbar action wrapping on tablet/phone widths. | Pages with many header actions should not overflow the viewport. | Complete |
| Added dense-table minimum widths for non-POS table scrollers. | Product, inventory, batch upload, and report tables scroll inside their wrapper instead of squeezing the whole page. | Complete |
| Kept POS cart table compact on desktop and phone. | POS should avoid unnecessary horizontal scroll at the counter. | Complete |
| Added phone-safe scanner modal sizing. | Scanner modal now fills phone width, removes desktop margins, and keeps the reader usable. | Complete |
| Added phone-safe payment dialog sizing. | Payment controls fit in a bottom-aligned scrollable panel on small screens. | Complete |
| Allowed auth/error pages to scroll on small screens. | Short mobile screens should not clip login or error guidance. | Complete |
| Added mobile nav label truncation. | Long mobile nav labels do not overlap neighboring items. | Complete |

## Files Changed

- `app/core/static/core/css/dashboard.css`
- `app/core/tests.py`
- `docs/versions/VERSION_COMPLETION_TRACKER.md`
- `docs/versions/v7/V7_TASKS.md`
- `docs/versions/v7/V7_MOBILE_TABLET_USABILITY_PASS.md`
- `docs/DEVELOPMENT_LOG.md`

## Verification

Run tests against the mounted working tree because the compose `web` service
does not bind-mount source code by default.

```bash
docker compose run --rm --no-deps -v "$PWD/app:/app" web python manage.py check
docker compose run --rm --no-deps -v "$PWD/app:/app" web python manage.py test core.tests.ScannerPlacementTests pos.tests.PosPageTests pos.tests.PaymentFlowTests catalog.tests.ProductDashboardTests inventory.tests.InventoryAdjustmentTests batch_upload.tests.BatchUploadViewTests --noinput --verbosity 1
docker compose run --rm --no-deps -v "$PWD/app:/app" web python manage.py test core.tests.DashboardShellTests core.tests.RoleAwareHomeTests core.tests.DashboardErrorPageTests core.tests.StyleguideAccessTests core.tests.AuthSettingsTests core.tests.ScannerPlacementTests pos.tests.PosPageTests pos.tests.QuickKeyTests pos.tests.PaymentFlowTests pos.tests.PromotionDashboardTests pos.tests.SalesCancellationTests core.tests.ScanResolveTests catalog.tests.ProductDashboardTests catalog.tests.ProductClassificationTests catalog.tests.ProductColumnFilterTests inventory labels reports audit system_logs batch_upload.tests.BatchUploadViewTests accounts.tests.UserManagementTests --noinput --verbosity 1
docker compose run --rm --no-deps -v "$PWD/app:/app" web python manage.py collectstatic --noinput
```

Result:

```text
System check identified no issues.
36 focused responsive tests OK.
140 mounted-source V7 regression tests OK.
collectstatic completed after CSS changes.
```

## Browser Verification

Temporary browser checks used a mounted-source Django runserver with explicit
host port mapping:

```bash
docker compose run --rm -p 8000:8000 -v "$PWD/app:/app" web python manage.py runserver 0.0.0.0:8000
```

Checked viewports:

| Viewport | Pages | Result |
| --- | --- | --- |
| Phone 390×844 | Dashboard, Products, POS, Stock-In, Inventory, Batch Upload | No document-level horizontal overflow; mobile nav visible; sidebar hidden. |
| Tablet 768×1024 | Dashboard, Products, POS, Inventory | No document-level horizontal overflow; mobile nav visible; sidebar hidden. |
| Desktop 1280×800 | Products, POS | No document-level horizontal overflow; desktop sidebar visible; mobile nav hidden. |
| Phone 390×844 scanner modal | Product scan modal | Full-width modal, no document overflow, reader height 220px. |

## Completion Rule

This task is complete. Future device-specific fixes should be attached to the
module they affect, unless they are broad release QA findings in V7-012.
