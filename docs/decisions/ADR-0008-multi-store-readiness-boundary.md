# ADR-0008: Multi-store Readiness Boundary

Status: Accepted
Date: 2026-06-16

## Context

V10 reviews future multi-store and scale-readiness needs. The current Melodu POS system is a single-store Django monolith with global catalog, stock, sales, reports, settings, roles, and audit records.

Introducing store/location fields without a complete migration, permission, report, and service plan could create data integrity and access-control risk.

## Decision

V10 is a planning and governance boundary only. It documents multi-store readiness, store/location model direction, store-level permissions, inventory/report/settings implications, operations hardening, retention, and performance risks.

No store model, foreign key, migration, store selector, permission behavior, route, template, report filter, or service mutation is introduced by V10.

## Consequences

| Consequence | Status |
| --- | --- |
| Current production remains safely single-store. | Current |
| Future multi-store work must start from an approved implementation task and migration plan. | Current |
| Store-level permissions and stock scoping must be designed together before UI exposure. | Current |
| V10 completion means planning completed, not multi-store implemented. | Current |

## Alternatives Considered

| Alternative | Decision |
| --- | --- |
| Add store fields immediately | Outdated for V10; too much migration and data risk without full approval. |
| Ignore multi-store until urgently needed | Outdated; planning now reduces future rework. |
| Split each store into a separate deployment/database | Future / Proposed only; current monolith can likely support first multi-store phase in one database if designed carefully. |

## Review Trigger

Review this ADR before any PR that adds `Store`, `Location`, store foreign keys, store-scoped permissions, store selectors, store-aware reports, store transfers, or per-store settings.

