# V7-006 Promotion And Label Page Polish

Status: Complete
Last updated: 2026-06-16

## Scope

V7-006 polished promotion and label pages while keeping the promotion pricing
engine, POS promotion selection, label rendering dimensions, audit creation,
permissions, and print behavior unchanged.

## Changes

| Change | Reason | Status |
| --- | --- | --- |
| Added a `Promotion Labels` action from the promotion list. | Staff can move from promotion management directly to offer label printing. | Complete |
| Added a promotion `Timeline` column. | Running, upcoming, ended, and inactive promotions are easier to distinguish without opening each record. | Complete |
| Added promotion form guidance and field help. | Staff need to understand discount type, value, product/category scope, no-stacking behavior, and below-cost risk. | Complete |
| Added scanner batch lookup to template-based `Print Labels`. | Label printing now matches the scan-first workflow available on Barcode / QR Print. | Complete |
| Added field help to product-label and promotion-label print forms. | Quantity and template selection are clearer before preview/print. | Complete |
| Added `Promotion Labels` cross-links from templates and promotion-label pages. | The label workflow is easier to navigate without returning to the sidebar. | Complete |

## Files Changed

- `app/pos/forms.py`
- `app/pos/views.py`
- `app/templates/pos/promotion_list.html`
- `app/templates/pos/promotion_form.html`
- `app/pos/tests.py`
- `app/labels/forms.py`
- `app/templates/labels/label_print.html`
- `app/templates/labels/promotion_label_print.html`
- `app/templates/labels/template_list.html`
- `app/labels/tests.py`
- `docs/versions/VERSION_COMPLETION_TRACKER.md`
- `docs/versions/v7/V7_TASKS.md`
- `docs/versions/v7/V7_PROMOTION_LABEL_PAGE_POLISH.md`
- `docs/DEVELOPMENT_LOG.md`

## Verification

Run tests against the mounted working tree because the compose `web` service
does not bind-mount source code by default.

```bash
docker compose run --rm --no-deps -v "$PWD/app:/app" web python manage.py check
docker compose run --rm --no-deps -v "$PWD/app:/app" web python manage.py test pos.tests.PromotionDashboardTests labels inventory.tests.BarcodePrintPageTests --noinput --verbosity 1
docker compose run --rm --no-deps -v "$PWD/app:/app" web python manage.py test core.tests.DashboardShellTests core.tests.RoleAwareHomeTests core.tests.StyleguideAccessTests core.tests.AuthSettingsTests pos.tests.PosPageTests pos.tests.QuickKeyTests pos.tests.PaymentFlowTests pos.tests.PromotionDashboardTests core.tests.ScanResolveTests core.tests.ScannerPlacementTests catalog.tests.ProductDashboardTests catalog.tests.ProductClassificationTests catalog.tests.ProductColumnFilterTests inventory labels --noinput --verbosity 1
```

Result:

```text
System check identified no issues.
18 promotion/label focused tests OK.
93 mounted-source V7 regression tests OK.
```

## Completion Rule

This task is complete. Future promotion or label behavior changes should keep
print layout changes explicit and covered by a tracked task.
