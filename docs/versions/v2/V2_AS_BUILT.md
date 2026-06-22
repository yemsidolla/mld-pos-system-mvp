# V2 As-Built Review — Stabilization, Safety, Reports, and Backup Baseline

## Summary

V2 added operational safety and documentation around the V1 build. Code changes
were surgical: report logic, backup scripts, dashboard auth UX, quick-create,
and POS polish.

## Implemented Features

| Feature | Status | Evidence |
| --- | --- | --- |
| V2 baseline audit docs | Implemented | `docs/legacy/V2_*` |
| Sellable-stock report inclusion | Implemented | Dev log + business rules |
| `expire_batches` command | Implemented | `inventory` management command |
| Backup/restore hardening | Implemented | `scripts/`, BACKUP_GUIDE |
| Dashboard login/logout | Implemented | `core/views.py`, Phase 2B |
| Quick-create API + modal | Implemented | Phase 2A |
| POS UX stabilization | Implemented | Phase 2B |

## Partially Implemented Features

| Feature | Status |
| --- | --- |
| Report exports | Documented Only — backlog item |

## Deferred / Not Implemented

Report export engine, OIDC, capability matrix.

## Permissions / Roles Impact

No new roles. Improved anonymous/wrong-role UX (redirect vs 403).

## Known Risks

| Risk | Notes |
| --- | --- |
| `expire_batches` not scheduled | Ops must run manually or via cron — Needs Verification |
| Legacy V2 docs in `docs/legacy/` | Duplicate / Overlapping with `docs/versions/v2/` |

## Handoff to Next Version

V3 — cost model, below-cost guardrails, promotions.
