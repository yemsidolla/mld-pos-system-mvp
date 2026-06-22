# V6 Rollback Plan

V6 is additive. Nothing in V6 deletes users, groups, roles, or audit data, so
rollback is a configuration change, not a data operation.

## Scenario 1 — Authentik is down or misconfigured (most common)

Staff cannot complete OIDC login. Two options, fastest first:

**a) Emergency local login (no deploy needed)**

```text
https://melodu-pos.khlovepet.com/dashboard/login/?local=1
```

Log in with the emergency local superuser. Existing staff with local
passwords can do the same while `LOCAL_LOGIN_ENABLED=True`.

**b) Switch the whole system back to local auth**

```bash
# on the prod host, edit .env:
AUTH_MODE=local
docker compose -f docker-compose.prod.yml up -d web
```

The login page reverts to the classic username/password form (V5 behavior).
OIDC-created users keep their roles but have unusable passwords — an admin
can set passwords at /dashboard/users/ if they must keep working during the
outage.

## Scenario 2 — group sync misbehaves but login is fine

```bash
OIDC_SYNC_GROUPS=False
docker compose -f docker-compose.prod.yml up -d web
```

Logins continue through Authentik; roles are managed manually in
/dashboard/users/ until the claim is fixed.

## Scenario 3 — full V6 code rollback

```bash
git checkout <pre-V6-commit>
docker compose -f docker-compose.prod.yml up -d --build
```

Safe because the only V6 migration (`audit.0005`) just widens choices —
older code reads the same tables without it. Do **not** roll back the
database.

## Invariants (verify after any rollback)

- [ ] At least one active local superuser exists and can log in
- [ ] Existing users/roles untouched (`/dashboard/users/`)
- [ ] Audit history intact (`/dashboard/audit-logs/`)
- [ ] `/health/` returns ok
