# V7-004 Catalog/Product List Polish

Status: Complete
Last updated: 2026-06-16

## Scope

V7-004 polished the dashboard product list while keeping catalog permissions,
product models, filters, image storage, batch upload behavior, and audit
behavior unchanged.

## Changes

| Change | Reason | Status |
| --- | --- | --- |
| Added a visible product search row above the product table. | Daily catalog work should not require opening the Product column filter just to search by name, code, barcode, or tag. | Complete |
| Kept the scan button next to the visible search field. | Staff can search from a physical code, camera scan, uploaded image decode, or manual typing from the same area. | Complete |
| Kept existing column filters and active-filter chips. | Power filtering still works for category, brand, classification, tag, and status. | Complete |
| Wrapped the product table in the shared horizontal table scroller. | Product lists have many columns and must remain usable on phone/tablet widths. | Complete |
| Strengthened the empty state with a clear reset/create-product path. | Empty result pages should tell staff what to do next. | Complete |
| Added a product-image render test. | Protects the Photo column after the recent product image work. | Complete |

## Files Changed

- `app/templates/catalog/product_list.html`
- `app/core/static/core/css/dashboard.css`
- `app/catalog/tests.py`
- `app/core/tests.py`
- `docs/versions/VERSION_COMPLETION_TRACKER.md`
- `docs/versions/v7/V7_TASKS.md`
- `docs/versions/v7/V7_CATALOG_PRODUCT_LIST_POLISH.md`
- `docs/DEVELOPMENT_LOG.md`

## Verification

Run tests against the mounted working tree because the compose `web` service
does not bind-mount source code by default.

```bash
docker compose run --rm --no-deps -v "$PWD/app:/app" web python manage.py check
docker compose run --rm --no-deps -v "$PWD/app:/app" web python manage.py test catalog.tests.ProductDashboardTests catalog.tests.ProductClassificationTests catalog.tests.ProductColumnFilterTests --noinput --verbosity 1
docker compose run --rm --no-deps -v "$PWD/app:/app" web python manage.py test core.tests.DashboardShellTests core.tests.RoleAwareHomeTests core.tests.StyleguideAccessTests core.tests.AuthSettingsTests pos.tests.PosPageTests pos.tests.QuickKeyTests pos.tests.PaymentFlowTests core.tests.ScanResolveTests core.tests.ScannerPlacementTests catalog.tests.ProductDashboardTests catalog.tests.ProductClassificationTests catalog.tests.ProductColumnFilterTests --noinput --verbosity 1
```

Result:

```text
System check identified no issues.
19 catalog-focused tests OK.
55 mounted-source V7 regression tests OK.
```

## Completion Rule

This task is complete. Do not remove the visible product search row, table
scroll wrapper, or product-image test unless a later catalog UX task explicitly
replaces them.
