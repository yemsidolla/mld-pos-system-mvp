# V7-011 English and Khmer Wording Consistency Review

Status: Complete
Last updated: 2026-06-16

## Scope

V7-011 reviewed and improved staff-facing English/Khmer wording for V7-touched
dashboard pages. It preserved existing workflows, routes, permissions, model
behavior, and business rules.

## Changes

| Change | Reason | Status |
| --- | --- | --- |
| Wrapped V7 Python-origin form/help/error strings with Django gettext. | Template strings were already translatable, but Python strings needed explicit gettext wrappers. | Complete |
| Added focused Khmer translations for V7 product, inventory, POS, batch upload, audit, logs, health, labels, promotions, and error-state wording. | Khmer mode now covers the most-used staff-facing V7 labels and guidance. | Complete |
| Compiled `django.mo` for the Khmer locale. | Runtime translation requires compiled gettext catalogs. | Complete |
| Added translation coverage tests for V7 strings and gettext-backed forms. | Future changes should not silently drop the translated V7 wording. | Complete |
| Browser-checked Khmer product, stock overview, and friendly 404/error pages. | Confirms the language switch works beyond direct gettext calls. | Complete |

## Files Changed

- `app/core/views.py`
- `app/core/permissions.py`
- `app/inventory/forms.py`
- `app/pos/forms.py`
- `app/labels/forms.py`
- `app/locale/km/LC_MESSAGES/django.po`
- `app/locale/km/LC_MESSAGES/django.mo`
- `app/core/tests.py`
- `docs/versions/VERSION_COMPLETION_TRACKER.md`
- `docs/versions/v7/V7_TASKS.md`
- `docs/versions/v7/V7_ENGLISH_KHMER_WORDING_REVIEW.md`
- `docs/DEVELOPMENT_LOG.md`

## Verification

Run tests against the mounted working tree because the compose `web` service
does not bind-mount source code by default.

```bash
msgfmt --check app/locale/km/LC_MESSAGES/django.po -o app/locale/km/LC_MESSAGES/django.mo
docker compose run --rm --no-deps -v "$PWD/app:/app" web python manage.py check
docker compose run --rm --no-deps -v "$PWD/app:/app" web python manage.py test core.tests.TranslationCoverageTests core.tests.DashboardShellTests core.tests.DashboardErrorPageTests inventory.tests.InventoryAdjustmentTests pos.tests.PromotionDashboardTests labels.tests.LabelTemplateAccessTests --noinput --verbosity 1
docker compose run --rm --no-deps -v "$PWD/app:/app" web python manage.py test core.tests.DashboardShellTests core.tests.RoleAwareHomeTests core.tests.DashboardErrorPageTests core.tests.StyleguideAccessTests core.tests.AuthSettingsTests core.tests.ScannerPlacementTests core.tests.TranslationCoverageTests pos.tests.PosPageTests pos.tests.QuickKeyTests pos.tests.PaymentFlowTests pos.tests.PromotionDashboardTests pos.tests.SalesCancellationTests core.tests.ScanResolveTests catalog.tests.ProductDashboardTests catalog.tests.ProductClassificationTests catalog.tests.ProductColumnFilterTests inventory labels reports audit system_logs batch_upload.tests.BatchUploadViewTests accounts.tests.UserManagementTests --noinput --verbosity 1
```

Result:

```text
msgfmt --check passed.
System check identified no issues.
29 focused translation/form/error tests OK.
142 mounted-source V7 regression tests OK.
```

## Browser Verification

Temporary browser checks used a mounted-source Django runserver with explicit
host port mapping:

```bash
docker compose run --rm -p 8000:8000 -v "$PWD/app:/app" web python manage.py runserver 0.0.0.0:8000
```

Checked:

| Page | Khmer Verification |
| --- | --- |
| Products | `html lang="km"`; product title, `New Product`, and `Search` rendered in Khmer. |
| Stock Overview | title, inventory lookup, and stock overview labels rendered in Khmer. |
| Friendly 404 | page title, `What to do next`, and no-technical-details footer rendered in Khmer. |

## Completion Rule

This task is complete for V7-touched screens. Full professional translation
review by a native Khmer reviewer remains a future content QA activity, not a
reason to reopen V7-011.
