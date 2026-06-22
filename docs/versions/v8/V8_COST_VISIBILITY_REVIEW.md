# V8 Cost Visibility Review

Status: Complete
Last updated: 2026-06-16

## Scope

V8-004 reviewed supplier reference costs, product default cost wording, stock-in actual/landed cost visibility, and role-based cost access.

## Changes

| Area | Change | Status |
| --- | --- | --- |
| Stock-in access | Added `costs_required` to stock-in so users without cost visibility cannot open a page that exposes actual/landed cost fields. | Current |
| Product cost wording | Added help text explaining product default cost as fallback cost and default selling price as stock-in starting point. | Current |
| Supplier reference cost wording | Renamed form label to `Supplier Reference Unit Cost` and explained that actual/landed costs are batch-specific. | Current |
| Reference cost list | Added product default cost and notes columns for cost comparison. | Current |
| Business rules | Updated `docs/reference/BUSINESS_RULES.md` with the cost terminology and stock-in visibility rule. | Current |

## Permission Decision

Stock-in remains `inventory.manage` gated and is now also cost-visibility gated. This matches Store Settings wording: unchecked roles get costs hidden everywhere. It prevents an inventory role with hidden costs from viewing or entering actual/landed costs.

## Validation

Commands:

```bash
docker compose run --rm --no-deps -v "$PWD/app:/app" web python manage.py test catalog.tests.ProductDashboardTests inventory.tests.StockInPageTests core.tests_cost_visibility.CostVisibilityPageTests --noinput --verbosity 2
docker compose run --rm --no-deps -v "$PWD/app:/app" web python manage.py test catalog.tests.MasterDataDashboardTests --noinput --verbosity 2
```

Results:

- 18 tests passed.
- 10 tests passed.

## Notes

- No database migration was added.
- No cost calculation order changed.
- POS below-cost logic remains part of V8-009.
