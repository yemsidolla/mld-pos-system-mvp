# Melodu POS V2 Roadmap

Date: 2026-06-09

## Summary

V2 begins with baseline documentation and V1 stabilization, not new feature work. The current V1 system is broad and tested, so the next risk is mixing product expansion with unresolved operational or business-rule ambiguity.

## Phase 0A: Baseline Audit

Status: complete in chat/read-only audit.

Goal:

- Inspect the repository and running local Docker stack without changing files.
- Confirm architecture, models, flows, permissions, deployment, tests, risks, and gaps.

Acceptance criteria:

- Audit covers architecture, apps, data model, POS, inventory, reports, scanner, batch upload, deployment, tests, risks, and recommendations.
- `python manage.py check` passes.
- Full Django test suite passes.
- Compose configs resolve to `postgres` and `web`.
- Audit reports whether files changed during Phase 0A.

## Phase 0B: Documentation Baseline

Status: complete.

Goal:

- Save the approved V2 baseline and operating rules in repo docs.

Deliverables:

- `docs/legacy/V2_BASELINE_AUDIT.md`
- `docs/legacy/V2_ROADMAP.md`
- `docs/reference/BUSINESS_RULES.md`
- `docs/operations/TESTING_CHECKLIST.md`
- `docs/operations/DEPLOYMENT_RUNBOOK.md`

Acceptance criteria:

- Docs describe the current V1 baseline accurately.
- Docs clearly state no internal Docker Nginx service is used.
- Docs avoid adding new business requirements.
- No code, schema, route, dependency, or migration changes.

## Phase 1: Existing V1 Stabilization

Status: implemented for audit-proven stabilization gaps.

Goal:

- Fix only issues proven by the audit or by user-reported V1 behavior.

Allowed work:

- POS sale/cart reliability.
- Stock batch invariants.
- Inventory adjustment/cancellation correctness.
- Role permission gaps.
- Dashboard operation gaps.
- Backup/restore clarity.
- iPhone/mobile verification.
- Test gaps around existing behavior.

Not allowed:

- New business modules.
- New public API surface.
- New dependencies unless required for a proven stabilization bug.

Defaults chosen for stabilization:

- Report inclusion: active products with active, non-expired, sellable stock.
- Expiry: explicit audited maintenance command, no scheduler dependency.
- Restore tests: monthly rehearsal on a non-production copy.

## Phase 2: V2 Feature Discovery

Status: documented in `docs/legacy/V2_FEATURE_BACKLOG.md`.

Goal:

- Build the owner-approved V2 feature backlog after V1 is stable.

Candidate feature families requiring owner approval:

- Customer accounts.
- Loyalty points.
- Promotions/discount rules.
- Multi-branch stock.
- Online payment integrations.
- External APIs.
- Mobile app.
- Report exports.

Acceptance criteria:

- Each feature has success criteria, affected workflows, data ownership, permission rules, test plan, and rollout plan before implementation.

## Phase 3: First V2 Feature Implementation

Goal:

- Implement only the first approved feature family.

Rules:

- One feature family at a time.
- Start with docs and tests.
- Keep existing V1 workflows working.
- Add migrations only after data model decisions are explicit.
- Verify with full test suite and browser/mobile smoke checks where relevant.

## Current Recommended Next Step

Freeze the V1 stabilization baseline, then implement the first approved V2 feature family from `docs/legacy/V2_FEATURE_BACKLOG.md`.
