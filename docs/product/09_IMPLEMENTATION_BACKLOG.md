# Implementation Backlog

Status: Implemented (documentation)
Last updated: 2026-06-16

This backlog is the preferred product-level task queue. `docs/TASKS.md` remains
the historical phase tracker.

Status labels: `Implemented`, `Partially Implemented`, `Documented Only`,
`Future / Proposed`, `Needs Verification`, `Outdated`, `Duplicate / Overlapping`.

## Task Format

Every implementation task should include:

```text
Task ID:
Title:
Module:
Version:
Business Reason:
Requirement:
Technical Scope:
Files likely affected:
Permission impact:
Data impact:
UI impact:
Docs impact:
Acceptance Criteria:
Test Cases:
Risk:
Definition of Done:
Status:
```

## Backlog Rules

| Rule | Status |
| --- | --- |
| Do not implement future work from this file without a user-approved task. | Current |
| Keep tasks small enough to test and document. | Current |
| Stock, sales, auth, permissions, and media changes require explicit tests. | Current |
| UI work must reference `docs/DESIGN_SYSTEM.md`. | Current |
| Completed implementation must update `docs/DEVELOPMENT_LOG.md`. | Current |
| Sidolla authorized sequential V7-V10 execution after planning; completed work must stay in the tracker as `Complete`. | Current |

## Current Governance Tasks

| ID | Task | Scope | Status | Notes |
| --- | --- | --- | --- | --- |
| GOV-001 | Create product documentation foundation | Docs only | Current | Completed by controlled foundation reset. |
| GOV-002 | Create V6 foundation reset docs | Docs only | Current | Completed by controlled foundation reset. |
| GOV-003 | Create ADR set | Docs only | Current | Completed by controlled foundation reset. |
| GOV-004 | Link README/current status/task tracker/development log to new docs | Docs only | Current | Completed by controlled foundation reset. |
| GOV-005 | Review legacy docs for overlap after reset | Docs only | Current | Legacy docs moved to `docs/legacy/` with cross-links updated. |
| GOV-006 | Create V7-V10 version planning docs and completion tracker | Docs only | Current | Version scopes, task checklists, QA checklists, release drafts, and durable tracker added. |
| GOV-007 | Reorganize docs folder into subfolders | Docs only | Current | `guides/`, `operations/`, `reference/`, `legacy/`, V6 auth into `versions/v6/`. |
| GOV-008 | Verify product foundation docs against codebase | Docs only | Implemented | `00_CURRENT_SYSTEM_MAP.md`, `04_MODULE_MAP.md`, `07_TRD.md` |
| GOV-009 | Rebuild product documentation foundation | Docs only | Implemented | Product docs 00–11, version PRD/TRD, ADR renumber, doc map |
| GOV-010 | Rebuild V1–V5 historical version docs | Docs only | Implemented | `docs/versions/v1/`–`v5/` full doc sets |

## Carry-Forward From V1–V5

| From | To | Item | Status |
| --- | --- | --- | --- |
| V1 | V6+ | Preserve batch-level inventory and audit foundation | Implemented — ADR-0003 |
| V2 | V9 | Improve report accuracy and owner visibility | Implemented |
| V2 | Ops | Backup/restore rehearsal on clone | Needs Verification |
| V3 | V8/V9 | Strengthen cost, below-cost, promotion reporting | Implemented |
| V4 | V8 | Improve label template and promotion label workflow | Implemented |
| V5 | V7 | Complete UI cleanup and staff workflow polish | Implemented |
| V5 | V7 | EN/Khmer wording consistency | Implemented |
| V4 | V6 | Formalize capability matrix and OIDC docs | Implemented |

## V7-V10 Version Backlog

| ID | Task | Scope | Status | Acceptance |
| --- | --- | --- | --- | --- |
| V7-PLAN-001 | UX/UI cleanup and staff workflow polish | UI/workflow | Implemented | V7 tasks are complete with evidence in `docs/versions/VERSION_COMPLETION_TRACKER.md`. |
| V8-PLAN-001 | Inventory, label, and promotion professionalization | Inventory/labels/promotions | Implemented | V8 tasks are complete with evidence in `docs/versions/VERSION_COMPLETION_TRACKER.md`. |
| V9-PLAN-001 | Reports, audit, and owner control | Reports/audit/ops | Implemented | V9 tasks are complete with evidence in `docs/versions/VERSION_COMPLETION_TRACKER.md`. |
| V10-PLAN-001 | Multi-store / scale-readiness foundation | Architecture/ops planning | Implemented (documentation) | V10 planning tasks are complete; no multi-store implementation was added. |

## Operational Verification Backlog

| ID | Task | Scope | Status | Acceptance |
| --- | --- | --- | --- | --- |
| OPS-VERIFY-001 | Verify host Nginx and Django production headers | Ops/docs | Needs Verification | Login, CSRF, secure cookies, static/media, health all pass on production domain. |
| OPS-VERIFY-002 | Rehearse PostgreSQL backup and restore | Ops/docs | Needs Verification | Restore into non-production clone and document result. |
| OPS-VERIFY-003 | Rehearse MinIO media backup and restore | Ops/docs | Needs Verification | Product/store/label images survive backup/restore in clone. |
| OPS-VERIFY-004 | Plan and test filesystem-media to MinIO migration | Ops/docs | Needs Verification | Existing media copied, references still resolve, rollback exists. |
| OPS-VERIFY-005 | Review dashboard live logs for secret exposure | Ops/security | Needs Verification | Common errors do not expose secrets, tokens, env values, or passwords. |

## Scanner And Hardware Backlog

| ID | Task | Scope | Status | Acceptance |
| --- | --- | --- | --- | --- |
| V7-SCAN-001 | Create production phone scanner matrix | QA/docs | Needs Verification | Test iOS Safari/Chrome and Android Chrome for camera and upload decode. |
| V7-SCAN-002 | Verify physical barcode scanner behavior | QA/docs | Future / Proposed | Scanner gun behaves as keyboard input in POS/stock-in/product forms. |
| V9-HW-001 | Certify receipt printer output | QA/docs | Future / Proposed | Real receipt printer output matches expected 80mm format. |
| V9-HW-002 | Certify label printer output | QA/docs | Future / Proposed | Product, stock batch, and promotion labels print correctly. |

## Reporting Backlog

| ID | Task | Scope | Status | Acceptance |
| --- | --- | --- | --- | --- |
| V8-RPT-001 | Confirm official report definitions | Product/docs | Future / Proposed | Owner approves date ranges, refunds/cancellations, payment types, cost/margin definitions. |
| V8-RPT-002 | Add export requirements for reports | Product/docs | Future / Proposed | Decide CSV, XLSX, PDF, or print output per report before implementation. |
| V8-RPT-003 | Define stock valuation report | Product/docs | Future / Proposed | Clarify whether actual cost, landed cost, or latest/reference cost is used. |
| V8-RPT-004 | Define end-of-day close workflow | Product/docs | Future / Proposed | Cashier/manager close steps and variance handling are documented. |

## Product Growth Backlog

| ID | Task | Scope | Status | Notes |
| --- | --- | --- | --- | --- |
| V10-GROW-001 | Customer profile and loyalty discovery | Product | Future / Proposed | No implementation until business flow is approved. |
| V10-GROW-002 | Supplier purchase order discovery | Product | Future / Proposed | Could extend stock-in, but must not bypass batch rules. |
| V10-GROW-003 | Payment integration discovery | Product/technical | Future / Proposed | Requires security and reconciliation planning. |
| V10-GROW-004 | Multi-store inventory discovery | Product/technical | Future / Proposed | Likely major schema/workflow change; ADR required. |
| V10-GROW-005 | Offline POS feasibility review | Product/technical | Future / Proposed | Major architecture risk; ADR required. |

## Parking Lot

| Idea | Status | Why Parked |
| --- | --- | --- |
| Replace Django templates with SPA | Future / Proposed | Current ADR favors Django monolith/templates. |
| Add Celery/Redis | Future / Proposed | No current workflow requires background queue infrastructure. |
| Import POS sales | Outdated | Conflicts with controlled workflow/audit model. |
| Import audit logs | Outdated | Audit logs must be generated by application actions. |
| Delete old docs during reset | Outdated | Legacy docs preserved under `docs/legacy/`. |
