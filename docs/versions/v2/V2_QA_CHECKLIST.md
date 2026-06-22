# V2 QA Checklist — Stabilization, Safety, Reports, and Backup Baseline

## Functional Checks

- [x] Stock summary excludes non-sellable batches per agreed rules — Implemented
- [x] `expire_batches` marks expired stock with audit — Implemented
- [x] Dashboard login works independently of Admin login — Implemented
- [x] Quick-create adds category/brand/supplier without losing form data — Implemented

## Permission Checks

- [x] Anonymous → login redirect; wrong role → 403 — Implemented

## Data Safety Checks

- [x] Restore script requires explicit confirmation — Implemented
- [ ] Restore rehearsal on clone — Needs Verification

## Report Checks

- [x] Low-stock uses sellable quantity logic — Implemented
- [ ] Export formats — Deferred

## Deployment Checks

- [x] Production checklist and runbook updated — Implemented

## Regression Risks

Report logic changes in V9 must preserve V2 sellable-stock definitions.
