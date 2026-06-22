# V7 Technical Requirements

Status: Complete
Last updated: 2026-06-16

## Allowed Changes

| Layer | Scope |
| --- | --- |
| Templates | Dashboard templates, partials, copy |
| CSS | `app/core/static/core/css/dashboard.css` — no token rewrite |
| JS | Small vanilla JS for UX only |
| Tests | View/template tests for changed routes |
| Docs | Version docs, development log |

## Forbidden Changes

Models, migrations, `permissions.py`, `capabilities.py`, `oidc.py`, business
services (`receive_stock`, `confirm_sale`, `cancel_sale`), report calculations.

## Design Authority

- `docs/DESIGN_SYSTEM.md`
- `docs/product/03_DESIGN_SYSTEM_AND_UX_RULES.md`
- `/dashboard/styleguide/` (Owner/Manager)

## Test Expectation

```bash
docker compose run --rm web python manage.py test
```

Targeted app tests for touched modules; V7 regression suite per tracker.

## Evidence

`docs/versions/VERSION_COMPLETION_TRACKER.md` — V7-001 through V7-012 Complete.
