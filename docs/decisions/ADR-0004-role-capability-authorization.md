# ADR-0004: Role And Capability Authorization

Status: Accepted
Date: 2026-06-16

## Context

The original Admin/Cashier split became too small for real store operations. The current system includes owner, manager, inventory staff, cashier, and viewer roles, with capability checks throughout dashboard workflows.

## Decision

Melodu POS will use role plus capability authorization.

`accounts.Role` defines baseline capabilities. `accounts.StaffProfile` assigns a user to a role and can add or revoke specific capabilities. Superusers resolve to Owner behavior. Legacy Admin and Cashier groups remain compatibility inputs.

## Consequences

| Consequence | Status |
| --- | --- |
| Dashboard navigation can be role-aware. | Current |
| Sensitive workflows can be independently gated. | Current |
| Cashier users can be restricted to POS-focused work. | Current |
| Owner-only operations can remain protected. | Current |
| New views must use capability decorators/helpers. | Current |

## Alternatives Considered

| Alternative | Decision |
| --- | --- |
| Two hard-coded roles only | Outdated; insufficient for manager/inventory/viewer separation. |
| Django permissions only | Future / Proposed only; current app uses business-facing capabilities. |
| Per-user checks everywhere | Outdated; harder to audit and maintain. |

## Review Trigger

Review this ADR if new business roles are added, if Django Admin permission exposure changes, or if capabilities become too granular to manage safely.
