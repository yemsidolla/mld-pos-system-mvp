# V7 QA Checklist

Status: Complete
Last updated: 2026-06-16

## Verification Summary

V7 QA passed with mounted-source Django checks, focused task tests, browser
phone/tablet/desktop smoke checks, Khmer language smoke checks, and release
documentation review.

Final broad regression evidence:

```text
System check identified no issues.
142 mounted-source V7 regression tests OK.
```

Additional browser evidence is recorded in:

- `docs/versions/v7/V7_MOBILE_TABLET_USABILITY_PASS.md`
- `docs/versions/v7/V7_ENGLISH_KHMER_WORDING_REVIEW.md`

## Scope Checklist

- [x] V7 work stayed UI/workflow polish only.
- [x] No data model, migration, POS logic, inventory logic, Auth/OIDC, or permission-model change was introduced.
- [x] No `docs/DESIGN_SYSTEM.md` rule change was introduced; CSS refinements reused existing dashboard patterns.

## Functional Checklist

- [x] Dashboard home renders for each role.
- [x] POS still supports scan/manual entry and sale completion.
- [x] Catalog/product pages still create/edit/search/filter.
- [x] Inventory and stock-in pages still work.
- [x] Promotion and label pages still render.
- [x] Reports still render.
- [x] Audit/log/system pages still render.

## Permission Checklist

- [x] Cashier sees only POS-focused workflows.
- [x] Inventory staff sees inventory/label workflows only as allowed.
- [x] Manager/Owner see management workflows.
- [x] No-role users receive the expected access-denied state.
- [x] Django Admin access behavior is unchanged.

## UI/UX Checklist

- [x] Page titles and nav labels are consistent.
- [x] Forms use shared form patterns.
- [x] Tables use shared table/filter/pagination patterns.
- [x] Primary and destructive actions are visually clear.
- [x] Empty/error/access-denied states are understandable.
- [x] Desktop and mobile layouts are checked.
- [x] English/Khmer wording is reviewed.

## Data Safety Checklist

- [x] No database schema changes.
- [x] No stock-changing service behavior changes.
- [x] No sale/cancellation/adjustment behavior changes.
- [x] No upload commit behavior changes.

## Audit/Logging Checklist

- [x] Existing audit events still fire for affected workflows.
- [x] No new logs expose secrets.
- [x] Permission denial behavior remains auditable where currently implemented.

## Documentation Checklist

- [x] `docs/versions/VERSION_COMPLETION_TRACKER.md` updated.
- [x] `docs/versions/v7/V7_TASKS.md` statuses updated.
- [x] `docs/DEVELOPMENT_LOG.md` updated.
- [x] Any changed user-facing guide updated only if behavior changed; V7 completion notes were added under `docs/versions/v7/`.

## Regression Checklist

- [x] Relevant Django view/template tests pass.
- [x] POS smoke test passes.
- [x] Catalog and inventory smoke tests pass.
- [x] Reports render smoke test passes.

## Release Checklist

- [x] All approved V7 tasks are complete or intentionally deferred.
- [x] Test results are recorded.
- [x] Manual UI checks are recorded.
- [x] Release note is finalized in `docs/versions/v7/V7_RELEASE_NOTE.md`.

## Rollback Checklist

- [x] UI/template/static changes can be reverted without data rollback.
- [x] No migration rollback needed.
- [x] Known visual regressions are documented; the temporary POS table overflow found during V7-010 browser QA was fixed before completion.
