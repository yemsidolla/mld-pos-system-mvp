# V8 Promotion Lifecycle Polish

Status: Complete
Last updated: 2026-06-16

## Scope

V8-008 polished promotion setup and lifecycle visibility. Pricing calculation order and POS best-promotion selection did not change.

## Changes

| Area | Change | Status |
| --- | --- | --- |
| Promotion list | Added total/running/upcoming/ended metrics. | Current |
| Promotion rows | Added human discount label, scope label, lifecycle detail, and below-cost badges. | Current |
| Promotion form | Grouped fields into identity, discount/dates, scope, and safety sections. | Current |
| Scope safety | Added form validation requiring either product or category, not both. | Current |
| Documentation | Updated business rules and promotion label guide. | Current |

## Rules Preserved

- Promotions do not stack.
- POS still chooses the best valid promotion by lowest final unit price.
- Promotion create/update/deactivate audit behavior remains in place.
- Below-cost promotion safety remains part of V8-009.

## Validation

Command:

```bash
docker compose run --rm --no-deps -v "$PWD/app:/app" web python manage.py test pos.tests.PromotionDashboardTests --noinput --verbosity 2
```

Result: 6 tests passed.

## Notes

Existing database rows with both product and category should be reviewed manually before editing because the dashboard form now requires a single scope.
