# V4 Scope — User Management, Classification, Printing, and Admin Maintenance

## Status

Historical / Completed

## Version Goal

Expand operational control: five roles, dashboard user management, product
classification, receipt/label printing, and safe data reset.

## Why This Version Existed

After V3 margin controls, the store needed proper staff access, richer product
metadata, professional printing, and maintenance tooling without Django Admin.

## In Scope

| Area | Status |
| --- | --- |
| Five roles: Owner, Manager, Inventory, Cashier, Viewer | Implemented |
| `StaffProfile` + legacy group compatibility | Implemented |
| Dashboard user management | Implemented |
| Capability-based page gating (precursor to full matrix) | Implemented |
| Product tags, animal type, life stage | Implemented |
| `StoreSetting` + 80mm thermal receipt | Implemented |
| `LabelTemplate` app + template CRUD/print | Implemented |
| Promotion label printing | Implemented |
| `reset_business_data` command with safety guards | Implemented |
| Receipt reprint with audit | Implemented |

## Out Of Scope

Full Authentik/OIDC production rollout, drag-and-drop label designer, dashboard
reset UI, multi-store reset.

## Source Evidence

- `docs/legacy/V4_PHASE_PLAN.md`
- `docs/DEVELOPMENT_LOG.md` — V4 Phases 1–6 (2026-06-09/10)
- `docs/reference/PERMISSION_MATRIX.md`

## Major Modules Affected

`accounts`, `core`, `catalog`, `labels`, `pos` (reprint), management commands

## Known Gaps

| Gap | Status |
| --- | --- |
| Capability matrix evolved further in V6 | Partially Implemented → V6 |
| Reset UI in dashboard | Deferred — CLI only |

## What Later Versions Should Improve

V5 UI polish, V6 OIDC + capability data model, V8 label workflow.
