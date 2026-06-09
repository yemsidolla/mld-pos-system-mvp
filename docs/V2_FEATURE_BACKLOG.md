# Melodu POS V2 Feature Backlog

Date: 2026-06-09

## Selection Rule

V2 features must build on stable V1 workflows. Prefer features that reuse existing models, reports, permissions, and tests before adding new data structures.

## Completed Phase 2A Slice: Inline Master-Data Quick Add

Status: implemented.

Delivered:

- Category and Brand quick-add from Product create/edit.
- Supplier quick-add from Stock-In.
- Admin-only JSON endpoint with CSRF protection.
- Audit logging and duplicate-name validation.

## Completed Phase 2B Slice: Dashboard Access And POS UX Stabilization

Status: implemented.

Delivered:

- Dashboard-specific login and POST-only logout flow.
- Friendly 403, 404, and 500 pages.
- Standardized Admin/Cashier/unassigned/inactive access behavior.
- POS empty states, checkout copy, and double-submit protection.
- Friendly invalid report date and batch-upload template handling.

## Priority 1: Report Exports

Default first V2 feature.

Goal:

- Add CSV export for existing reports before adding new report types.

Reason:

- Low schema risk.
- Builds on existing report queries.
- Helps owners verify sales, stock, expiry, movement, and staff sales data outside the app.

Acceptance criteria:

- Existing HTML reports continue working.
- CSV export is available only to Admin users.
- CSV output uses the same filters and business rules as the HTML report.
- Tests cover permission, content type, headers, and at least one data row per export.

## Priority 2: Receipt And Report Print Hardening

Goal:

- Make receipt and report print views more reliable without introducing PDF dependencies.

Acceptance criteria:

- Receipt print layout works at common printer widths.
- Report print layout remains readable.
- Browser smoke checks cover desktop and mobile.

## Priority 3: Customer Profiles

Goal:

- Add optional customer identity on sales only after report exports are stable.

Required decisions before implementation:

- Required customer fields.
- Whether anonymous sales remain default.
- Phone number uniqueness.
- Customer data retention policy.

## Priority 4: Promotions And Discount Rules

Goal:

- Replace manual discount entry with controlled promotion rules.

Required decisions before implementation:

- Promotion types.
- Stacking rules.
- Expiry dates.
- Role allowed to create promotions.
- Audit requirements.

## Priority 5: Multi-Branch Stock

Goal:

- Support more than one store/warehouse location.

Required decisions before implementation:

- Branch model ownership.
- Stock transfer rules.
- Sale branch assignment.
- User branch permissions.
- Migration plan for existing stock.

## Deferred

- Online payment gateway integration.
- Public external APIs.
- Mobile app.
- Loyalty points.
- Celery/Redis/background workers.

These are deferred until the owner confirms business rules and operational support.
