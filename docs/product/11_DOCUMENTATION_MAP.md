# Documentation Map

Status: Implemented (documentation)
Last updated: 2026-06-16

This is the authority map for Melodu POS documentation. For folder layout see
`docs/README.md`.

## Status Labels

Use these labels in product and version docs:

| Label | Meaning |
| --- | --- |
| Implemented | Built and in current codebase |
| Partially Implemented | Exists but incomplete or needs verification |
| Documented Only | Planned in docs, not built |
| Future / Proposed | Intentional later work |
| Needs Verification | Exists but production/device proof missing |
| Outdated | Superseded; kept for history |
| Duplicate / Overlapping | Multiple docs cover same topic |

## Required Read Order

1. `docs/STANDARD_WAY_OF_WORKING.md`
2. `README.md`
3. `docs/product/00_CURRENT_SYSTEM_MAP.md`
4. `docs/product/08_VERSION_ROADMAP.md`
5. `docs/versions/v1/V1_SCOPE.md` through `docs/versions/v5/V5_SCOPE.md` (historical)
6. `docs/versions/v6/V6_SCOPE.md` (foundation reset)
7. `docs/versions/v7/` onward (current/future planning)
8. `docs/product/05_BRD.md`
9. `docs/product/06_PRD.md`
10. `docs/product/07_TRD.md`
11. `docs/product/09_IMPLEMENTATION_BACKLOG.md`
12. `docs/product/10_QA_RELEASE_PROCESS.md`
13. `docs/DESIGN_SYSTEM.md` if UI is affected
14. `docs/product/03_DESIGN_SYSTEM_AND_UX_RULES.md` for workflow UX context
15. Relevant `docs/decisions/ADR-*.md`
16. `docs/CURRENT_STATUS.md` for compact handoff
17. `docs/DEVELOPMENT_LOG.md` for change history

## Authority Rules

| Question | First source | Supporting sources |
| --- | --- | --- |
| How should work be done? | `docs/STANDARD_WAY_OF_WORKING.md` | `docs/product/02_TEAM_GOVERNANCE_AND_DELIVERY_RULES.md`, `docs/product/10_QA_RELEASE_PROCESS.md` |
| What exists in code now? | `docs/product/00_CURRENT_SYSTEM_MAP.md` | `docs/CURRENT_STATUS.md`, `docs/product/04_MODULE_MAP.md` |
| What should UI look like? | `docs/DESIGN_SYSTEM.md` | `docs/product/03_DESIGN_SYSTEM_AND_UX_RULES.md`, `docs/guides/DASHBOARD_UX_GUIDE.md` |
| Business needs? | `docs/product/05_BRD.md` | `docs/reference/BUSINESS_RULES.md` |
| Product behavior? | `docs/product/06_PRD.md` | Version PRDs, guides |
| Technical constraints? | `docs/product/07_TRD.md` | ADRs, `docs/guides/`, `docs/versions/v6/` auth docs |
| What work is next? | `docs/product/09_IMPLEMENTATION_BACKLOG.md` | `docs/TASKS.md`, `docs/versions/VERSION_COMPLETION_TRACKER.md` |
| Version plan? | `docs/product/08_VERSION_ROADMAP.md` | `docs/versions/vN/VN_SCOPE.md` |
| Historical evolution? | `docs/versions/v1/`–`v5/` | `docs/legacy/`, `docs/DEVELOPMENT_LOG.md` |
| Why a foundation choice? | `docs/decisions/` | Relevant version TRDs |

## Product Foundation Docs

| Path | Purpose |
| --- | --- |
| `00_CURRENT_SYSTEM_MAP.md` | Codebase-verified system map |
| `01_PRODUCT_VISION_AND_OPERATING_MODEL.md` | Vision, users, workflows, boundaries |
| `02_TEAM_GOVERNANCE_AND_DELIVERY_RULES.md` | Roles, DoR, DoD, change control |
| `03_DESIGN_SYSTEM_AND_UX_RULES.md` | Workflow UX rules (links to DESIGN_SYSTEM) |
| `04_MODULE_MAP.md` | Module-by-module bridge to technical planning |
| `05_BRD.md` | Business requirements |
| `06_PRD.md` | Product requirements and acceptance |
| `07_TRD.md` | Technical requirements and architecture |
| `08_VERSION_ROADMAP.md` | V6–V10 themes |
| `09_IMPLEMENTATION_BACKLOG.md` | Task backlog format and queue |
| `10_QA_RELEASE_PROCESS.md` | QA and release gates |
| `11_DOCUMENTATION_MAP.md` | This file |

## Version Docs (per folder)

Each `docs/versions/vN/` should contain:

- `VN_SCOPE.md`
- `VN_PRD.md`
- `VN_TRD.md`
- `VN_TASKS.md`
- `VN_QA_CHECKLIST.md`
- `VN_RELEASE_NOTE.md`

V6 also includes auth/OIDC supporting docs (`V6_AUTHENTIK_*`, checklists, etc.).

Historical versions V1–V5: `docs/versions/v1/` through `docs/versions/v5/` — each
contains `VN_SCOPE.md`, `VN_AS_BUILT.md`, `VN_TASKS.md`, `VN_QA_CHECKLIST.md`,
`VN_RELEASE_NOTE.md`.

## ADRs

| ADR | Topic |
| --- | --- |
| `ADR-0001-django-monolith.md` | Django monolith |
| `ADR-0002-authentik-oidc-strategy.md` | Authentik/OIDC |
| `ADR-0003-batch-level-inventory.md` | Batch-level inventory |
| `ADR-0004-role-capability-authorization.md` | Role + capability auth |
| `ADR-0005-label-template-strategy.md` | Label templates |
| `ADR-0006-dashboard-design-system.md` | Dashboard design system |
| `ADR-0007-standard-way-of-working.md` | Standard way of working |
| `ADR-0008-multi-store-readiness-boundary.md` | Multi-store readiness boundary |

## Supporting Doc Folders

| Folder | Purpose |
| --- | --- |
| `docs/guides/` | Operator/developer how-to guides |
| `docs/operations/` | Runbooks and checklists |
| `docs/reference/` | Business rules, permissions, project spec |
| `docs/legacy/` | Historical V2–V5 phase docs |

## Legacy Handling

- Do not delete legacy docs without explicit approval
- Prefer this map to resolve overlaps
- Mark uncertain behavior as **Needs Verification**
