# ADR-0007: Standard Way Of Working

Status: Accepted
Date: 2026-06-16

## Context

Melodu POS has grown quickly through AI-assisted and human-guided implementation. To keep future work safe, every contributor needs the same expectations for reading context, planning, changing code, testing, documenting, and releasing.

## Decision

`docs/STANDARD_WAY_OF_WORKING.md` is the first-read governance document for future Melodu POS work.

It defines how requirements, scope, design-system changes, implementation, testing, documentation updates, and releases must be handled. This foundation reset adds a documentation map, product docs, version docs, and ADRs around that standard.

## Consequences

| Consequence | Status |
| --- | --- |
| Future AI/human contributors have a clear starting point. | Current |
| Documentation changes are part of implementation, not optional cleanup. | Current |
| Scope control is explicit; new requirements need user approval. | Current |
| Work can be resumed more safely across sessions and contributors. | Current |

## Alternatives Considered

| Alternative | Decision |
| --- | --- |
| Keep relying on chat history only | Outdated; too fragile for long-running product work. |
| Use only `docs/TASKS.md` | Duplicate / Overlapping; useful tracker but not enough governance. |
| Rewrite all old docs | Outdated for this reset; cross-linking is safer. |

## Review Trigger

Review this ADR if the team changes its development workflow, adds a formal release manager, changes AI tooling expectations, or moves to a multi-repository product structure.
