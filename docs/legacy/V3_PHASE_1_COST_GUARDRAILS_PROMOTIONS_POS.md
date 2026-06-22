# Melodu POS V3 Phase 1

Date: 2026-06-09

## Name

V3 Phase 1 - Cost Model, Sales Guardrails, Simple Promotions, And Responsive POS

## Purpose

Protect shop margin, support real supplier/batch cost differences, prevent cashier mistakes, allow owner-approved discounts, and improve POS usability on desktop, tablet, and mobile.

## Delivered Scope

- Added supplier/product reference costs at `/dashboard/reference-costs/`.
- Replaced batch `cost_price` with `actual_unit_cost` and optional `landed_unit_cost`.
- Added cost-basis priority for sale validation:
  1. `landed_unit_cost` when present.
  2. `actual_unit_cost` when greater than zero.
  3. supplier/product reference cost, then product default cost.
- Added SaleItem snapshots for stock batch, reference cost, actual cost, landed cost, cost basis, original price, final price, discount, promotion, and admin override details.
- Added below-cost sale guardrails:
  - Cashier is blocked.
  - Admin can override only with a reason.
  - Promotion can sell below cost only when `allow_below_cost` is enabled.
- Added simple Admin-managed promotions at `/dashboard/promotions/`.
- Supported promotion discount types:
  - Percentage.
  - Fixed amount.
  - Fixed final price.
- Applied one best valid promotion per product; promotions do not stack.
- Added audit logging for cost changes, stock batch cost changes, below-cost sales, admin overrides, promotion changes, and below-cost promotion sales.
- Improved POS responsive behavior with clearer cart states, promotion labels, double-submit protection, sticky desktop cart, and touch-friendly quantity steppers.

## Current Exclusions

- Purchase orders.
- Supplier payment tracking.
- Customer loyalty or membership pricing.
- Coupon codes.
- Bundles, BOGO, or stacked promotions.
- Multi-branch stock.
- Multi-currency.
- Accounting integrations.
- Return/refund workflow.
- Mobile app.

## Verification

Run:

```bash
docker compose -f docker-compose.yml -f docker-compose.local.yml config --services
docker compose -f docker-compose.prod.yml config --services
docker compose -f docker-compose.yml -f docker-compose.local.yml exec -T web python manage.py check
docker compose -f docker-compose.yml -f docker-compose.local.yml exec -T web python manage.py makemigrations --check --dry-run
docker compose -f docker-compose.yml -f docker-compose.local.yml exec -T web python manage.py test
docker compose -f docker-compose.yml -f docker-compose.local.yml exec -T web python manage.py collectstatic --noinput
```

Expected compose services remain:

```text
postgres
web
```

No internal Docker Nginx service is used.
