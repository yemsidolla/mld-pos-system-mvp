# V6 Deployment Checklist

Deploy in two stages: ship the code with `AUTH_MODE=local` first (zero
behavior change), then flip to OIDC once Authentik is verified.

## Stage A — ship V6 code (no auth change)

- [ ] Backup: `scripts/backup_db.sh` (and media if relevant)
- [ ] `git pull` on the prod host
- [ ] Confirm `.env`: `AUTH_MODE=local`, **`DJANGO_DEBUG=False`** (was found
      True in prod on 2026-06-11 — must never ship True)
- [ ] `docker compose -f docker-compose.prod.yml up -d --build`
- [ ] `docker compose -f docker-compose.prod.yml exec web python manage.py migrate`
- [ ] `docker compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput`
- [ ] `docker compose -f docker-compose.prod.yml restart web` — **required after
      collectstatic**: WhiteNoise caches the static manifest at process start,
      so without a restart the app keeps serving the previous JS/CSS hashes
- [ ] `curl -s https://melodu-pos.khlovepet.com/health/` → `"status": "ok"`
- [ ] Login/logout works exactly as before (classic form)

## Stage B — Authentik cutover

Prerequisites (from `docs/V6_AUTHENTIK_SETUP_GUIDE.md`):

- [ ] Authentik live at https://auth.khlovepet.com (initial-setup done, MFA on admins)
- [ ] Groups `melodu-admin/manager/inventory/cashier/report-viewer` created
- [ ] Each staff member assigned to exactly one group
- [ ] OIDC provider + application `melodu-pos` created; redirect URI
      `https://melodu-pos.khlovepet.com/oidc/callback/`
- [ ] Authentik DB backup configured

Cutover:

- [ ] Verify the emergency local superuser can log in **before** switching
- [ ] Set in `.env`: `AUTH_MODE=oidc`, `OIDC_RP_CLIENT_ID`,
      `OIDC_RP_CLIENT_SECRET`, the five `OIDC_OP_*` endpoint URLs
      (keep `LOCAL_LOGIN_ENABLED=True`)
- [ ] `docker compose -f docker-compose.prod.yml up -d web`
- [ ] Login page shows "Continue with Melodu Staff Login"
- [ ] Test login per role: admin → full dashboard; cashier → POS only;
      a user with no melodu-* group → "No role assigned" page
- [ ] Audit log shows LOGIN_SUCCESS / USER_AUTOCREATED / GROUP_SYNC rows
- [ ] Logout returns to login (and ends SSO session if
      `OIDC_OP_LOGOUT_ENDPOINT` is set)
- [ ] Emergency path still works: `/dashboard/login/?local=1`

## If anything fails

`docs/V6_ROLLBACK_PLAN.md` — Scenario 1: set `AUTH_MODE=local`, restart web.
