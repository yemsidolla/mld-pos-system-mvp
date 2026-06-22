# V7 Release Note

Status: Complete
Last updated: 2026-06-16

## Version Summary

V7 improves the daily staff experience through dashboard UX/UI cleanup,
responsive layout hardening, clearer empty/error states, and focused
English/Khmer wording coverage.

## What Changed

- Cleaned up dashboard navigation labels and workflow naming.
- Polished the dashboard home quick actions while keeping role-aware visibility.
- Fixed POS quick keys so they submit original barcodes and hide unusable no-barcode products.
- Improved the product list with visible search, scan/search controls, photo rendering protection, table scroll, and stronger empty states.
- Improved stock-in and inventory pages with clearer help text, receive-another shortcuts, low-stock level badges, batch open actions, and batch action guidance.
- Improved promotion and label pages with promotion label links, promotion timeline status, print form help text, and scan lookup on label printing.
- Improved report readability with metric summaries, lateral report/action links, table scroll wrappers, and status/severity badges.
- Improved audit, live log, and system health pages with read-only metrics, human-readable system health values, log safety guidance, and clearer operator panels.
- Improved empty/error/access-denied states with safe `What to do next` guidance and stronger no-data states.
- Hardened mobile/tablet usability for topbar actions, dense tables, scanner modal, payment dialog, auth/error pages, and mobile navigation.
- Added focused Khmer translations for V7-touched staff-facing strings and compiled the Khmer gettext catalog.

## What Did Not Change

- No new inventory logic.
- No new POS payment behavior.
- No promotion engine rewrite.
- No report calculation changes.
- No model, migration, Auth/OIDC, or permission-model changes.
- No design-system rewrite unless separately approved.

## Risk Level

Medium. UI changes can affect workflows, role visibility, and staff speed even
without data changes. V7 mitigated this through targeted tests, broader
regression runs, and browser layout checks.

## Testing Notes

Final verification evidence:

```text
msgfmt --check passed.
System check identified no issues.
142 mounted-source V7 regression tests OK.
```

Browser checks covered:

- Phone 390×844: dashboard, products, POS, stock-in, inventory, batch upload.
- Tablet 768×1024: dashboard, products, POS, inventory.
- Desktop 1280×800: products, POS.
- Phone scanner modal sizing.
- Khmer language switch on Products, Stock Overview, and friendly 404 pages.

## Rollback Note

Rollback should be a code/UI/static/locale revert only. No database rollback is
needed because V7 introduced no migrations or data-model changes.

## Recommended Next Version

V8 - Inventory, Label, and Promotion Professionalization.

## Completion Evidence

- `docs/versions/VERSION_COMPLETION_TRACKER.md`
- `docs/versions/v7/V7_QA_CHECKLIST.md`
- V7 task completion notes in `docs/versions/v7/`
