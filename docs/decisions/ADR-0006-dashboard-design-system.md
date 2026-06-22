# ADR-0006: Dashboard Design System

Status: Accepted
Date: 2026-06-16

## Context

Melodu POS moved daily work out of Django Admin into a custom merchant dashboard. Consistency matters because staff need to work quickly across POS, catalog, inventory, upload, reports, labels, and system pages.

## Decision

The dashboard will use a shared design system documented in `docs/DESIGN_SYSTEM.md`. UI changes should extend or reuse the shared shell, navigation, buttons, forms, badges, tables, cards, alerts, modals, filters, and scanner patterns.

This ADR does not duplicate design rules. `docs/DESIGN_SYSTEM.md` remains the design authority.

## Consequences

| Consequence | Status |
| --- | --- |
| Dashboard pages should look and behave consistently. | Current |
| Product and workflow pages should avoid one-off inline UI patterns. | Current |
| Mobile views and scanner affordances must be considered in UI changes. | Current |
| UI work requires design-system documentation review. | Current |

## Alternatives Considered

| Alternative | Decision |
| --- | --- |
| Use Django Admin for all workflows | Outdated; daily UX requirements exceed Admin. |
| Add React/SPA design system | Future / Proposed only; not part of current architecture. |
| Let every page define its own style | Outdated; creates inconsistent staff experience. |

## Review Trigger

Review this ADR if the frontend architecture changes, a component library is adopted, or major UI redesign work is approved.
