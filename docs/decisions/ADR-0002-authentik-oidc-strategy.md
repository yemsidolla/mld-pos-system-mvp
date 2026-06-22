# ADR-0002: Authentik OIDC Strategy

Status: Accepted
Date: 2026-06-16

## Context

The system started with local Django login. V6 added optional Authentik/OIDC support so production staff access can be centrally managed while preserving a recovery path.

## Decision

Melodu POS supports two authentication modes:

- `AUTH_MODE=local`: local Django username/password login.
- `AUTH_MODE=oidc`: Authentik/OIDC login through `mozilla_django_oidc` and `accounts.oidc.MeloduOIDCBackend`.

Local login remains available as an emergency path when `LOCAL_LOGIN_ENABLED=True`.

OIDC group names map to Melodu roles, including Owner, Manager, Inventory Staff, Cashier, and Viewer.

## Consequences

| Consequence | Status |
| --- | --- |
| Production can use SSO without removing local recovery access too early. | Current |
| Role assignment can sync from Authentik groups when configured. | Current |
| Superuser behavior remains protected from accidental OIDC downgrade. | Current |
| Production OIDC group claim behavior must be verified before fully relying on sync. | Needs Verification |

## Alternatives Considered

| Alternative | Decision |
| --- | --- |
| Local login only forever | Future / Proposed only for simple deployments; less central control. |
| OIDC-only with no local fallback | Outdated until production OIDC recovery is fully verified. |
| Custom auth provider | Outdated; Authentik/OIDC is standard enough for this need. |

## Review Trigger

Review this ADR if local login is disabled in production, if Authentik is replaced, or if external identity groups no longer match store roles.
