# V6 Phase 0 — Current Authentication & Permission Audit

Audited: 2026-06-11 (V5 codebase, commit `d4434bf`).
Every statement below was verified against the actual code, not assumed.

## 1. Authentication today

| Aspect | Implementation |
|---|---|
| Login | Local username/password, `AuthenticationForm`, at `/dashboard/login/` (`core/views.py::dashboard_login_view`) |
| Logout | POST-only `/dashboard/logout/` (`core/views.py::dashboard_logout_view`) |
| Session | `django.contrib.sessions` (DB backend), cookie flags from env |
| Django Admin | Enabled at `/admin/`, blocked for cashiers by `core.middleware.CashierAdminBlockMiddleware` |
| MFA / SSO / password policy | None beyond Django's default `AUTH_PASSWORD_VALIDATORS` |
| OIDC / external IdP | None — no library installed (`app/requirements.txt`) |

`dashboard_login_view` validates `next` with `url_has_allowed_host_and_scheme` (open-redirect safe).

## 2. Authorization today

**The single source of truth for roles is `accounts.models.StaffProfile.role`**, not
Django groups and not Django model permissions.

Resolution order (`core/permissions.py::get_user_role`):

1. Inactive/anonymous → no access (`None`)
2. `is_superuser` → `OWNER`
3. `staff_profile.role` → that role
4. Legacy group `Admin` → `MANAGER`; legacy group `Cashier` → `CASHIER`
5. Otherwise → `None` (no dashboard access)

Roles: `OWNER`, `MANAGER`, `INVENTORY`, `CASHIER`, `VIEWER`.

Capability functions (`can_manage_users`, `can_manage_inventory`, `can_view_reports`,
`can_reset_data`, …) plus view decorators (`@admin_required`, `@inventory_required`,
`@users_required`, …) wrap `dashboard_role_required`, which redirects anonymous users
to login and renders a friendly 403 (`dashboard/error.html`) otherwise.
**55 decorator usages** across view modules — coverage is consistent.

Findings:

- **Django model permissions (`has_perm`) are not used anywhere.** Authorization is
  pure role-capability functions. This is good for V6: Authentik group sync should
  target `StaffProfile.role`, not Django permission objects.
- **Only two Django groups exist** (`Admin`, `Cashier`), kept for backward
  compatibility ("map and keep") and synced on user save
  (`accounts/views.py::_sync_legacy_group`); created on `post_migrate`
  (`accounts/signals.py`).
- One inconsistency: `catalog_quick_create_view` uses `@login_required` + a manual
  `is_admin_user` JSON 403 instead of a capability decorator (works, but differs in style).

## 3. Existing safety rails (keep — do not regress)

- **Owner lockout protection**: `_active_owner_count` refuses to deactivate/demote the
  last active Owner (`accounts/views.py`).
- Self-protection: cannot change own role or disable own account.
- Manager cannot edit an Owner or superuser (`PermissionDenied`).
- Only an Owner can assign the Owner role.
- Sale cancellation requires a reason (`pos/views.py:266`); below-cost sale requires
  `override_reason` (`pos/views.py:166`).
- Data reset is **CLI-only**: `core/management/commands/reset_business_data.py`, double-gated
  by `ALLOW_DATA_RESET` env flag and audit-logged. There is no web UI for it.
- `setup_roles` command bootstraps groups + an admin superuser (used for fresh DBs).

## 4. Audit logging today

`audit.AuditLog` already captures: user, action, module, object refs, old/new JSON,
IP (X-Forwarded-For aware), user agent, timestamp. Signals log `LOGIN_SUCCESS` and
`LOGIN_FAILED` (`audit/signals.py`). `ROLE_CHANGE`, `DEACTIVATE`, `SETTING_CHANGE`,
`DATA_RESET` and POS/stock actions are logged in views/services.

Missing for V6: `LOGOUT`, `USER_AUTOCREATED` (OIDC first login), `GROUP_SYNC` /
profile-sync, `PERMISSION_DENIED` events.

## 5. Configuration & deployment

- Single `app/melodu_pos/settings.py`, env-driven via `python-dotenv`; no settings split.
- `SECRET_KEY` has a dev fallback default (acceptable; prod sets it via env).
- Prod compose builds the image locally; **no entrypoint runs `migrate`** — manual step
  per `docs/operations/DEPLOYMENT_RUNBOOK.md`. `/health/` reports unapplied migrations.
- **Observed in production on 2026-06-11: `DJANGO_DEBUG=True` was set** (full debug
  pages exposed publicly). Must be `False` before/with V6 deploy.
- External Nginx + Cloudflare in front; WhiteNoise serves static.

## 6. Gaps vs. V6 goals

| # | Gap | Impact on V6 |
|---|---|---|
| 1 | No OIDC support | Phase 3 adds `mozilla-django-oidc` |
| 2 | No `Manager`/`Inventory`/`Report Viewer` Django groups | Phase 1 seeds 5 groups matching Authentik `melodu-*` groups |
| 3 | Role authority is `StaffProfile`, not groups | Group sync must write `StaffProfile.role` (and legacy groups) — mapping to Django groups alone would do nothing |
| 4 | No logout/auto-create/group-sync audit actions | Phase 5 extends `AuditLog.Action` |
| 5 | Login page is local-only | Phase 3/6 adds "Continue with Melodu Staff Login" (OIDC) + emergency local form |
| 6 | No friendly "no role assigned" page | Exists partially (403 page); needs the no-access state for auto-created users |
| 7 | `DEBUG=True` seen in prod | Fix env now, document in deployment checklist |

## 7. Role-name mapping decision (important)

The V6 spec names roles `Admin / Manager / Cashier / Inventory / Report Viewer`.
The codebase's real roles are `OWNER / MANAGER / INVENTORY / CASHIER / VIEWER`.
To avoid breaking 55 working permission checks, **V6 maps Authentik groups onto the
existing StaffProfile roles** instead of renaming anything:

| Authentik group | StaffProfile role | Legacy Django group synced |
|---|---|---|
| `melodu-admin` | `OWNER` | `Admin` |
| `melodu-manager` | `MANAGER` | `Admin` |
| `melodu-inventory` | `INVENTORY` | — |
| `melodu-cashier` | `CASHIER` | `Cashier` |
| `melodu-report-viewer` | `VIEWER` | — |

A user with none of these groups logs in successfully but has **no role → no access**
(friendly page), matching the spec's fallback requirement. Local superusers are never
demoted by sync.

## 8. Verdict

The V5 permission layer is clean, centralized, and consistently applied — **no
structural cleanup is required before Authentik integration**. The work is additive:
seed groups, add OIDC backend + group→role sync, extend audit actions, and improve the
login/error UI. The main design constraint is that sync must drive `StaffProfile.role`
(Section 7), because Django groups are not the authority in this codebase.
