# V8 POS Promotion Safety Polish

Status: Complete
Last updated: 2026-06-16

## Scope

V8-009 improved POS promotion and below-cost visibility. It did not change pricing calculation, promotion selection, override permission checks, or sale confirmation services.

## Changes

| Area | Change | Status |
| --- | --- | --- |
| POS cart summary | Added promotion discount total alert when cart contains promoted items. | Current |
| POS line item | Added was/now price display and per-line savings under promotion name. | Current |
| Below-cost warning | Added cashier-facing manager approval warning before checkout. | Current |
| Admin override warning | Added admin-facing reminder to enter override reason before completing below-cost sale. | Current |
| Allowed below-cost promotion | Added warning when a promotion is explicitly allowed to sell below cost. | Current |

## Rules Preserved

- POS still chooses the best valid promotion by lowest final unit price.
- Cashiers still cannot confirm unauthorized below-cost sales.
- Admin below-cost override still requires a written reason.
- Promotion-enabled below-cost sale still requires `allow_below_cost`.
- Sale item snapshots and audit behavior did not change.

## Validation

Command:

```bash
docker compose run --rm --no-deps -v "$PWD/app:/app" web python manage.py test pos.tests.PosPageTests pos.tests.PosServiceTests pos.tests.PaymentFlowTests --noinput --verbosity 2
```

Result: 25 tests passed.

## Notes

The UI now explains promotion savings before sale confirmation. The sale service remains the authority for validation and audit.
