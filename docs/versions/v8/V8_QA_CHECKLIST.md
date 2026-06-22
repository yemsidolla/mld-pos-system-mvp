# V8 QA Checklist

Status: Complete
Last updated: 2026-06-16

## Scope Checklist

- [x] V8 stayed within inventory, labels, barcode/QR, promotions, and related audit/visibility scope.
- [x] No multi-store, procurement, accounting, Auth/OIDC, or global role-model work was added.
- [x] Any stock logic change had explicit task approval.

## Functional Checklist

- [x] Stock-in still creates batches, barcode/QR, movement, and audit.
- [x] Stock overview and batch detail show correct stock and expiry states.
- [x] Adjustments still require reason and prevent negative stock.
- [x] Barcode/QR print workflows still work.
- [x] Label templates can be managed and printed.
- [x] Promotion setup and POS visibility work.
- [x] Below-cost warnings/overrides remain safe.

## Permission Checklist

- [x] Inventory workflows remain capability-gated.
- [x] Cost visibility follows configured role/capability behavior.
- [x] Promotion and label pages remain capability-gated.
- [x] Cashier cannot access management-only inventory/label/cost screens.

## UI/UX Checklist

- [x] Stock states are visually clear.
- [x] Label workflow distinguishes barcode/QR, product, shelf, and promotion labels.
- [x] Promotion lifecycle states are clear.
- [x] Inventory movement traceability is easy to find.
- [x] Desktop/mobile layouts remain usable.

## Data Safety Checklist

- [x] No negative stock path introduced.
- [x] Existing batch quantities remain consistent.
- [x] Movement ledger remains complete.
- [x] Sale item to stock batch links remain unchanged.
- [x] Any migration has explicit approval and test coverage.

## Audit/Logging Checklist

- [x] Stock-in, adjustment, print, and promotion changes are audited where expected.
- [x] Movement records include correct quantities and references.
- [x] No secrets are logged.

## Documentation Checklist

- [x] Tracker and V8 task statuses updated.
- [x] Inventory/label/promotion guides updated if behavior changed.
- [x] Development log updated.
- [x] Release note finalized.

## Regression Checklist

- [x] Inventory tests pass.
- [x] POS promotion tests pass if POS display/behavior changed.
- [x] Labels tests pass.
- [x] Permission/cost visibility tests pass.
- [x] Full suite considered for stock or pricing changes.

## Release Checklist

- [x] All approved V8 tasks complete/deferred.
- [x] Physical print checks recorded if relevant: browser print pages render; real label-printer output remains `Needs Verification` before production label stock changes.
- [x] Test results recorded.
- [x] Rollback plan understood.

## Rollback Checklist

- [x] UI-only changes can be reverted safely.
- [x] Data/service changes have migration/rollback notes if applicable.
- [x] Label template changes have backup/export or manual recreation plan if data changed.

## Verification Evidence

| Check | Result |
| --- | --- |
| `docker compose run --rm --no-deps -v "$PWD/app:/app" web python manage.py check` | Passed, no issues. |
| Full mounted-source Django suite | Passed, 311 tests OK. |
| `docker compose run --rm --no-deps -v "$PWD/app:/app" web python manage.py collectstatic --noinput` | Passed, static files collected/post-processed. |
| Browser desktop smoke | Passed for stock overview, stock movements, label templates, label print, barcode/QR print, promotions, and POS. No dashboard shell errors or horizontal overflow detected. |
| Browser phone-width smoke | Passed at 390px width for the same V8 pages. Mobile navigation present, no page/main overflow detected. |
| Browser console | No JavaScript errors captured during V8 smoke pass. |

## Notes

- No database migrations were introduced by V8.
- V8 intentionally did not add multi-store, procurement, accounting, new payment methods, or Auth/OIDC behavior.
- Physical printer output still needs real-device verification before changing live label stock/templates in production.
