# V9-005 Promotion And Below-cost Reporting

Status: Complete
Last updated: 2026-06-16

## Purpose

Give the owner a read-only report for promotion impact and risky below-cost sale lines.

## Definitions

| Signal | Definition | Status |
| --- | --- | --- |
| Promotion usage | Completed sale items where `promotion_name_at_sale` is populated. | Current |
| Gross | `original_unit_price * quantity` from sale-item snapshots. | Current |
| Discount | `discount_amount * quantity` from sale-item snapshots. | Current |
| Final sales | `SaleItem.subtotal` from completed sale-item snapshots. | Current |
| Below-cost line | Promoted sale item where `final_unit_price < cost_basis_at_sale`. | Current |
| Override | Promoted sale item with `override_by` set. | Current |
| Cost/margin | Snapshot cost and margin, visible only when cost visibility allows it. | Current |

## Implementation

- Added `reports.views.promotion_report_view`.
- Added route `dashboard/reports/promotions/` named `promotion-report`.
- Added `app/templates/reports/promotion_report.html`.
- Added Reports index link.
- Updated `app/reports/tests.py`.

## What Changed

- Added Promotion & Below-cost Report under Reports.
- Grouped promotion impact by the promotion name saved on sale items.
- Added below-cost review table linking back to sale detail.
- Used existing sale-item snapshots only; no historic sales are recalculated from current promotion rules.

## What Did Not Change

- No promotion pricing logic changed.
- No POS sale confirmation logic changed.
- No cost visibility rule changed.
- No database migrations were introduced.

## Verification

```bash
docker compose run --rm --no-deps -v "$PWD/app:/app" web python manage.py test reports.tests.ReportPageTests --noinput --verbosity 1
```

Result: 15 tests OK.
