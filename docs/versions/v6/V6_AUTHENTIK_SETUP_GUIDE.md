# V6 Authentik Setup Guide

Authentik is the central identity provider for Melodu staff at
`https://auth.khlovepet.com`. It answers *"who is this user and can they access
Melodu?"* — Django keeps answering *"what can this user do inside Melodu?"*
(see `docs/versions/v6/V6_AUTHENTIK_AUTH_ARCHITECTURE.md`).

## 1. Deploy the Authentik stack

Files in this repo:

- `docker-compose.authentik.yml` — Authentik server + worker + its own Postgres 16 + Redis 7
- `.env.authentik.example` — copy to `.env.authentik` and fill in secrets

```bash
cp .env.authentik.example .env.authentik
openssl rand -base64 48   # → AUTHENTIK_SECRET_KEY
openssl rand -base64 24   # → AUTHENTIK_PG_PASS
docker compose -f docker-compose.authentik.yml --env-file .env.authentik up -d
```

The server listens on `127.0.0.1:9000` only — external Nginx terminates HTTPS.
Authentik uses **its own Postgres** (`./data/authentik/postgres`), fully separate
from the POS database, so either system can be restored/rebuilt independently.

First-run setup (create the `akadmin` password):

```text
https://auth.khlovepet.com/if/flow/initial-setup/
```

## 2. Nginx reverse proxy (auth.khlovepet.com)

Authentik needs WebSocket upgrade support:

```nginx
map $http_upgrade $connection_upgrade {
    default upgrade;
    ''      close;
}

server {
    listen 443 ssl http2;
    server_name auth.khlovepet.com;

    ssl_certificate     /etc/letsencrypt/live/auth.khlovepet.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/auth.khlovepet.com/privkey.pem;

    client_max_body_size 16m;

    location / {
        proxy_pass http://127.0.0.1:9000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;
    }
}

server {
    listen 80;
    server_name auth.khlovepet.com;
    return 301 https://$host$request_uri;
}
```

If Cloudflare proxies this hostname, set SSL mode to **Full (strict)**.

## 3. Create staff groups

In Authentik Admin → **Directory → Groups**, create:

```text
melodu-admin
melodu-manager
melodu-inventory
melodu-cashier
melodu-report-viewer
```

These map to Melodu roles per `docs/versions/v6/V6_PERMISSION_MATRIX.md`. Assign each staff
member to exactly one group (highest wins if several).

## 4. Create the OIDC provider + application

**Applications → Providers → Create → OAuth2/OpenID Provider**

| Setting | Value |
|---|---|
| Name | `Melodu POS Provider` |
| Authorization flow | `default-provider-authorization-implicit-consent` (no consent screen for staff) |
| Client type | `Confidential` |
| Client ID / Secret | auto-generated — copy both into the POS `.env` |
| Redirect URIs | `https://melodu-pos.khlovepet.com/oidc/callback/` and `http://127.0.0.1:8000/oidc/callback/` (local dev) |
| Signing key | `authentik Self-signed Certificate` |
| Scopes | `openid`, `email`, `profile` (authentik's default `profile` scope mapping already includes the `groups` claim) |

**Applications → Applications → Create**

| Setting | Value |
|---|---|
| Name | `Melodu POS` |
| Slug | `melodu-pos` |
| Provider | `Melodu POS Provider` |

Optionally restrict who can even start a login: on the application, add a
**policy binding** for each `melodu-*` group so non-staff Authentik accounts
are rejected at the door.

### Resulting endpoints (used by Django settings)

```text
Issuer:        https://auth.khlovepet.com/application/o/melodu-pos/
Authorization: https://auth.khlovepet.com/application/o/authorize/
Token:         https://auth.khlovepet.com/application/o/token/
Userinfo:      https://auth.khlovepet.com/application/o/userinfo/
JWKS:          https://auth.khlovepet.com/application/o/melodu-pos/jwks/
End session:   https://auth.khlovepet.com/application/o/melodu-pos/end-session/
```

## 5. MFA and password policy

- **MFA**: Flows & Stages → edit the authentication flow, add a TOTP /
  WebAuthn stage. Start with admins/managers, then roll out to all staff.
- **Password policy**: Customization → Policies → password policy (length ≥ 12),
  bind it to the password-change flow.
- Keep the default **enrollment flows disabled** — staff accounts are created by
  an admin, never self-registered.

## 6. Backups

Back up three things (the POS backup scripts in `scripts/` do NOT cover Authentik):

```bash
# 1. Authentik database
docker compose -f docker-compose.authentik.yml exec authentik-postgres \
  pg_dump -U authentik authentik | gzip > backups/authentik-$(date +%F).sql.gz

# 2. Media + certs
tar czf backups/authentik-data-$(date +%F).tgz data/authentik/media data/authentik/certs

# 3. .env.authentik (contains AUTHENTIK_SECRET_KEY — losing it invalidates sessions/tokens)
```

## 7. Security hardening checklist

- [ ] `AUTHENTIK_SECRET_KEY` is random ≥ 48 bytes and never committed
- [ ] Port 9000 bound to `127.0.0.1` only (no direct internet exposure)
- [ ] **No Docker socket mounted** — if an outpost later needs Docker access, use
      `tecnativa/docker-socket-proxy` with minimal permissions and document why
- [ ] `akadmin` has a strong password + MFA; create named admin accounts and keep
      `akadmin` as break-glass only
- [ ] Application policy bindings restrict login to `melodu-*` groups
- [ ] Error reporting disabled (`AUTHENTIK_ERROR_REPORTING__ENABLED=false`)
- [ ] Authentik updated on a schedule (`AUTHENTIK_TAG` pinned, bumped deliberately)
- [ ] Backups tested with a restore drill

## 8. If Authentik is down

Melodu POS keeps a local emergency login (see `docs/versions/v6/V6_ROLLBACK_PLAN.md`):
set `AUTH_MODE=local` in the POS `.env` and restart the web container, or use the
always-available local form at `/dashboard/login/?local=1` with the emergency
Django superuser.
