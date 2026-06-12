# V6 Authentication Architecture

## Principle

```text
Authentik answers: Who is this user and can they access Melodu?
Django answers:    What can this user do inside Melodu?
```

Authentik (auth.khlovepet.com) owns identity: central staff login, SSO, MFA,
password policy, account lifecycle, group membership. Django keeps every
business rule: StaffProfile roles, capability checks, audit logs, POS/stock
rules. Business permissions are **never** moved into Authentik — Authentik
group names only select which Melodu role a user gets.

## Login flow (AUTH_MODE=oidc)

```text
User → melodu-pos.khlovepet.com/dashboard/
  → Django: not authenticated → /dashboard/login/
  → "Continue with Melodu Staff Login" → /oidc/authenticate/
  → Authentik authorize (auth.khlovepet.com, MFA/policies apply)
  → /oidc/callback/  (mozilla-django-oidc)
  → MeloduOIDCBackend (app/accounts/oidc.py):
      - match local user by username, then email; auto-create if allowed
      - sync email / first / last name from claims
      - deny inactive users (audited LOGIN_FAILED)
      - sync melodu-* groups → StaffProfile.role + legacy Django groups
  → Django session established → /dashboard/
```

Library: **mozilla-django-oidc** — a plain Django auth backend, the smallest
maintainable option; no allauth machinery, no hand-rolled token handling.

## Group → role mapping

See `docs/V6_PERMISSION_MATRIX.md`. Sync rules (fail-safe by design):

- highest melodu-* group wins; claim **present but empty** clears the role
  (user lands on the friendly "No role assigned" page);
- claim **absent** keeps existing roles and logs a warning — a misconfigured
  claim cannot strip the whole staff of access;
- superusers are never modified; `OIDC_SYNC_GROUPS=False` disables sync for
  manual role management; every change is audited (`GROUP_SYNC`).

## Emergency access

- `ModelBackend` is always active: the local form lives at
  `/dashboard/login/?local=1` while `LOCAL_LOGIN_ENABLED=True`.
- Keep one local Django superuser with a strong password (and ideally
  restrict who knows it). Django admin at `/admin/` is unchanged.
- Full recovery procedure: `docs/V6_ROLLBACK_PLAN.md`.

## Audit coverage

`LOGIN_SUCCESS`, `LOGIN_FAILED` (incl. inactive OIDC denials), `LOGOUT`,
`USER_AUTOCREATED`, `GROUP_SYNC`, `PERMISSION_DENIED`, plus the existing
`ROLE_CHANGE` / `DEACTIVATE` / `SETTING_CHANGE` / `DATA_RESET` trail.
Each row stores user, action, timestamp, IP (X-Forwarded-For aware),
user agent, and object/old/new JSON values.

## Configuration

All via env (see `.env.example`): `AUTH_MODE`, `LOCAL_LOGIN_ENABLED`,
`OIDC_RP_CLIENT_ID/SECRET`, `OIDC_OP_*` endpoints, `OIDC_GROUPS_CLAIM`,
`OIDC_AUTO_CREATE_USER`, `OIDC_SYNC_GROUPS`. `AUTH_MODE=local` (default)
reproduces V5 behavior exactly — that is the rollback switch.
