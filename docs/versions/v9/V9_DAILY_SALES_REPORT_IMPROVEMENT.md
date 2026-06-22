# V9-002 Daily Sales Report Improvement

Status: Complete
Last updated: 2026-06-16

## Purpose

Make the daily sales report clearer for owner cash/control review without changing sale creation, cancellation, or payment behavior.

## Definition

| Item | Definition | Status |
| --- | --- | --- |
| Completed revenue | Sum of `Sale.final_amount` for sales with `status=COMPLETED` on the selected date. | Current |
| Gross sales | Sum of `Sale.total_amount` for completed sales on the selected date. | Current |
| Discounts | Sum of `Sale.discount_amount` for completed sales on the selected date. | Current |
| Cancelled sales | Counted as exceptions, not revenue. | Current |
| Payment breakdown | Completed sales only, grouped by `Sale.payment_method`. | Current |
| Cost of goods | Sum of `SaleItem.cost_basis_at_sale * quantity` for completed sale items on the selected date. | Current |
| Gross margin | Completed revenue minus cost of goods. | Current |
| Cost visibility | Cost and margin are shown only when `core.permissions.can_view_costs()` allows the user. | Current |

## Implementation

- Updated `app/reports/views.py::daily_sales_report_view`.
- Updated `app/templates/reports/daily_sales.html`.
- Updated `app/reports/tests.py`.

## What Changed

- Added report definition guidance directly on the page.
- Added completed sales, cancelled sales, completed revenue, average sale, gross sales, and discount metric cards.
- Added cost of goods and gross margin metric cards for users allowed to view costs.
- Added payment-method breakdown for completed sales.
- Linked sale numbers to sale detail so exceptions can be inspected.
- Kept the detail table inclusive of completed and cancelled sales so exceptions remain visible.

## What Did Not Change

- No sale totals are mutated.
- No sale cancellation logic changed.
- No payment methods changed.
- No export formats were added.
- No database migrations were introduced.

## Verification

```bash
docker compose run --rm --no-deps -v "$PWD/app:/app" web python manage.py test reports.tests.ReportPageTests --noinput --verbosity 1
```

Result: 12 tests OK.
