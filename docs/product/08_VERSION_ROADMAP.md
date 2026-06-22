# Version Roadmap

Status: Implemented (documentation)
Last updated: 2026-06-16

This roadmap separates **historical versions (V1–V5)**, **foundation reset
(V6)**, and the tracked V7–V10 completion path.

## Roadmap Summary

### Historical Versions (Completed)

| Version | Theme | Status | Docs |
| --- | --- | --- | --- |
| V1 | MVP POS & Inventory Foundation | Implemented | `docs/versions/v1/` |
| V2 | Stabilization, Safety, Reports, and Backup Baseline | Implemented | `docs/versions/v2/` |
| V3 | Cost Control, Pricing Rules, and Promotion Foundation | Implemented | `docs/versions/v3/` |
| V4 | User Management, Classification, Printing, and Admin Maintenance | Implemented | `docs/versions/v4/` |
| V5 | UI/UX Polish, Naming Cleanup, and Product Usability | Implemented (partial mobile slice) | `docs/versions/v5/` |

### Foundation / Current Reset

| Version | Theme | Status | Docs |
| --- | --- | --- | --- |
| V6 | Foundation Reset & Access Control | Implemented (documentation) | `docs/versions/v6/` |

### Tracked Versions

| Version | Theme | Status | Docs |
| --- | --- | --- | --- |
| V7 | UX/UI Cleanup & Staff Workflow | Complete | `docs/versions/v7/` |
| V8 | Inventory, Label, and Promotion Professionalization | Complete | `docs/versions/v8/` |
| V9 | Reports, Audit, and Owner Control | Complete | `docs/versions/v9/` |
| V10 | Multi-store / SaaS-readiness Foundation | Complete (planning only) | `docs/versions/v10/` |

## Historical Version Summaries

### V1 — MVP POS & Inventory Foundation

Built Django monolith, batch inventory, POS, reports, audit, ops pages, deployment
baseline. Late V1 added dashboard shell, batch upload, scanner, product CRUD.

**Keep:** batch-level stock, movement ledger, audit trail.

### V2 — Stabilization, Safety, Reports, and Backup Baseline

Documented as-built system; hardened backup/restore; corrected sellable-stock
reports; `expire_batches`; dashboard login UX.

**Carry forward:** report definitions → V9; restore rehearsal → ops backlog.

### V3 — Cost Control, Pricing Rules, and Promotion Foundation

Reference costs, batch actual/landed costs, below-cost guardrails, promotions,
SaleItem snapshots, MinIO option.

**Carry forward:** promotion/cost reporting → V8/V9.

### V4 — User Management, Classification, Printing, and Admin Maintenance

Five roles, user management, classification, store/receipt settings, label
templates, promotion labels, safe CLI reset.

**Carry forward:** label workflows → V8; capabilities → V6 formalized.

### V5 — UI/UX Polish, Naming Cleanup, and Product Usability

Nav cleanup, audit log page, list pagination, workflow shortcuts, partial mobile
polish. Did not fully solve staff UX satisfaction.

**Carry forward:** remaining polish → V7.

## V6: Foundation Reset & Access Control

Documentation foundation, ADRs, Authentik/OIDC as-built docs, capability registry.
No heavy UI coding in V6 scope.

## V7-V10

See `docs/versions/VERSION_COMPLETION_TRACKER.md` for task-by-task evidence.
V7, V8, and V9 include implemented application improvements. V10 is complete
as a planning/scale-readiness package only; it does not implement multi-store
schema, permissions, routes, templates, or services.

## ADR Cross-Links

| ADR | Historical relevance |
| --- | --- |
| ADR-0001 Django Monolith | V1 foundation |
| ADR-0002 Authentik/OIDC | V6; auth prep in V4/V5 era |
| ADR-0003 Batch-level Inventory | V1/V2/V3 — permanent |
| ADR-0004 Role Capability Authorization | V4 origin → V6 formalized |
| ADR-0005 Label Template Strategy | V4 origin → V8 improvements |
| ADR-0006 Dashboard Design System | V5 prep → V7 enforcement |
| ADR-0007 Standard Way of Working | V6+ all work |
| ADR-0008 Multi-store Readiness Boundary | V10 scale-readiness boundary |

## Legacy Docs

Older phase plans remain in `docs/legacy/` as Duplicate/Overlapping supporting
evidence. Prefer `docs/versions/v1/`–`v5/` for historical version context.
