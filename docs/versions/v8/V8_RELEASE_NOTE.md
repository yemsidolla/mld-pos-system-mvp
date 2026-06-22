# V8 Release Note

Status: Complete
Last updated: 2026-06-16

## Version Summary

V8 professionalizes inventory, label, barcode/QR, promotion, and stock-traceability workflows while preserving the current Django monolith, batch-level stock rules, and role/capability model.

## What Changed

- Added an inventory workflow audit and documented the current stock safety model.
- Improved Stock Overview and Stock Batch Detail with clearer quantity, expiry, supplier, generated-code, movement, and action context.
- Improved low-stock and expiry reports with reorder gaps, expiry days, supplier context, and next-action labels.
- Tightened stock-in access to respect configured cost visibility because receiving stock requires cost entry.
- Clarified supplier reference cost, product default cost, and stock-in actual/landed cost wording.
- Improved barcode/QR print with selected-batch checks, custom-code guidance, and scanner quality hints.
- Improved label template management with template metrics, field summaries, grouped form sections, and guide updates.
- Improved product/shelf and promotion label print pages with setup warnings, preview metrics, and print-dialog actions.
- Improved promotion list/form lifecycle clarity and added validation that a promotion targets either a product or a category, not both.
- Improved POS promotion visibility with savings, below-cost, manager approval, and admin override warnings.
- Improved stock movement reporting with search/type filters, product code, custom code, gated batch links, and gated audit links.

## What Did Not Change

- No multi-store stock transfer.
- No advanced procurement module.
- No accounting integration.
- No complex campaign engine.
- No new POS payment methods.
- No Auth/OIDC or global role-model changes.
- No database migrations.

## Risk Level

Medium. V8 touched stock, cost, label, and promotion visibility, but it did not change the core stock deduction, stock-in service, sale confirmation, or batch movement model.

## Testing Notes

- Mounted-source `manage.py check` passed.
- Full mounted-source Django test suite passed: 311 tests OK.
- Focused inventory, reports, label, promotion, POS, audit, scanner, and cost-visibility tests passed during V8 tasks.
- `collectstatic --noinput` passed after CSS/template changes.
- Browser desktop smoke passed for stock overview, stock movements, label templates, label print, barcode/QR print, promotions, and POS.
- Browser phone-width smoke passed at 390px for the same V8 pages with mobile navigation present and no page/main overflow detected.
- Browser console had no JavaScript errors during the V8 smoke pass.
- Real physical label-printer output remains `Needs Verification` before production label stock/template changes.

## Rollback Note

Most V8 changes are templates, view context, forms, tests, and documentation. Revert the V8 commit set normally if needed. No schema rollback is required because V8 introduced no migrations. If existing promotions already have both product and category selected, review them manually before editing because V8 now enforces one scope per promotion in the dashboard form.

## Recommended Next Version

V9 - Reports, Audit, and Owner Control.
