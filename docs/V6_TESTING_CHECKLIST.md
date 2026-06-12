# V6 Testing Checklist

## Automated (run inside Docker)

```bash
docker compose -f docker-compose.yml -f docker-compose.local.yml up -d --build
docker compose -f docker-compose.yml -f docker-compose.local.yml exec web python manage.py collectstatic --noinput
docker compose -f docker-compose.yml -f docker-compose.local.yml exec web python manage.py check
docker compose -f docker-compose.yml -f docker-compose.local.yml exec web python manage.py test
```

Status 2026-06-12: **226 tests, all passing** (`manage.py check`: no issues).

V6 coverage lives in `app/accounts/tests_oidc.py`:

| Spec requirement | Test |
|---|---|
| Login through mocked OIDC response | `OIDCCallbackFlowTests.test_mocked_oidc_login_creates_user_and_logs_in` |
| Local user auto-created | same test + `OIDCBackendSyncTests.test_create_user_sets_identity_role_and_audit` |
| Existing user updated | `test_update_user_syncs_identity_and_role_change` |
| Authentik groups → Django roles/groups | `GroupRoleMappingTests`, `test_create_user_…` |
| Removed group removes mapped role/group | `test_removed_group_clears_role_and_access` |
| No group → no dashboard access | `test_user_without_melodu_group_gets_no_access_page` |
| Cashier blocked from admin pages | `PermissionDeniedAuditTests.test_cashier_blocked_…` (+ V5 suites) |
| Inventory user can open inventory | `test_inventory_user_can_open_inventory` |
| Manager-only below-cost override | V5 `pos.tests` (confirm_sale guard) |
| Sensitive action needs permission | V5 suites + `PermissionDeniedAuditTests` |
| Friendly permission-denied page | `test_user_without_melodu_group_gets_no_access_page`, `core.tests.DashboardAuthTests` |
| Emergency local superuser usable | `test_emergency_local_superuser_can_still_login` |
| Inactive user denied | `test_inactive_user_denied_with_audit` |
| Missing groups claim fail-safe | `test_missing_groups_claim_keeps_existing_role` |
| Sync disable switch | `test_sync_disabled_never_touches_roles` |
| Superuser protected from sync | `test_superuser_never_modified_by_sync` |

## Manual (against local Docker, then production)

- [ ] `AUTH_MODE=local`: classic form, login/logout, no SSO button
- [ ] `AUTH_MODE=oidc` + real Authentik: SSO round-trip per role
      (admin / manager / inventory / cashier / report-viewer)
- [ ] User in no melodu-* group → "No role assigned" page
- [ ] `?local=1` emergency form works; `LOCAL_LOGIN_ENABLED=False` hides it
- [ ] Wrong OIDC client secret → friendly error on login page (no traceback)
- [ ] Audit log rows: LOGIN_SUCCESS, LOGOUT, USER_AUTOCREATED, GROUP_SYNC,
      PERMISSION_DENIED
- [ ] Profile dropdown shows name, role badge, logout on desktop + mobile
- [ ] Login/error pages render correctly on iPhone (LAN URL)
