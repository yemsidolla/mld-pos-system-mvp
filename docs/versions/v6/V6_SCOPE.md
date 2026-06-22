# V6 Scope: Foundation Reset & Access Control

Status: Implemented (documentation)
Last updated: 2026-06-17

## Summary

V6 Foundation Reset is a documentation and governance reset around the existing Melodu POS build. It does not change application behavior, database schema, routes, permissions, templates, CSS, scripts, or runtime configuration.

The goal is to make the current system understandable before the next implementation cycle.

## In Scope

| Item | Status |
| --- | --- |
| Create product-level current system map. | Current |
| Create product vision and operating model. | Current |
| Create module map. | Current |
| Create BRD, PRD, and TRD. | Current |
| Create version roadmap. | Current |
| Create implementation backlog. | Current |
| Create QA and release process. | Current |
| Create documentation map and read order. | Current |
| Create V6 scope, as-built review, task list, QA checklist, and release note draft. | Current |
| Create ADRs for foundation decisions. | Current |
| Update README, current status, task tracker, and development log with links/status. | Current |

## Out Of Scope

| Item | Status | Notes |
| --- | --- | --- |
| App behavior changes | Outdated | Explicitly forbidden for this reset. |
| Source code changes | Outdated | No app code should change. |
| Model/schema/migration changes | Outdated | No database behavior should change. |
| Route or URL changes | Outdated | No public interface behavior changes. |
| Permission/auth/OIDC behavior changes | Outdated | Document only. |
| Template/CSS/design-system changes | Outdated | `docs/DESIGN_SYSTEM.md` remains unchanged. |
| Reset scripts or backup script changes | Outdated | Document only. |
| Deleting or archiving older docs | Outdated | Keep and cross-link older docs. |
| Implementing V7/V8/V9/V10 work | Future / Proposed | Roadmap/backlog only. |

## Acceptance Criteria

| Criteria | Status |
| --- | --- |
| `docs/product/` contains all required foundation documents. | Current |
| `docs/versions/v6/` contains all required V6 reset documents. | Current |
| `docs/decisions/` contains ADR-0001 through ADR-0007. | Current |
| README includes a compact documentation map section. | Current |
| `docs/CURRENT_STATUS.md` points to the new authoritative maps and removes stale local-change notes. | Current |
| `docs/TASKS.md` tracks the reset. | Current |
| `docs/DEVELOPMENT_LOG.md` records the reset milestone. | Current |
| Git diff confirms only docs/README paths changed. | Needs Verification |
| Django tests are not run because the change is Markdown-only. | Current |

## Source Of Truth Used

| Source | Status |
| --- | --- |
| Django settings and URL routing | Current |
| Installed apps and models | Current |
| Services, permissions, OIDC backend, middleware | Current |
| Dashboard templates and static workflow docs | Current |
| Management commands and scripts | Current |
| Existing docs and development log | Current |

## Reset Result

After this reset, future work should start from:

1. `docs/STANDARD_WAY_OF_WORKING.md`
2. `README.md`
3. `docs/CURRENT_STATUS.md`
4. `docs/product/11_DOCUMENTATION_MAP.md`
5. `docs/product/00_CURRENT_SYSTEM_MAP.md`
6. Relevant version/guide/backlog docs
