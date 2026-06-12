# V6 Permission Matrix

Roles are stored in `accounts.models.StaffProfile.role` and resolved by
`core/permissions.py::get_user_role`. Django superusers are always Owner.
Legacy groups `Admin` → Manager and `Cashier` → Cashier still resolve for
pre-V4 accounts ("map and keep").

## Role matrix (verified against view decorators)

| Capability | Owner | Manager | Inventory | Cashier | Viewer | Enforced by |
|---|:-:|:-:|:-:|:-:|:-:|---|
| Open dashboard shell | ✅ | ✅ | ✅ | ✅ | ✅ | `@dashboard_required` |
| POS sale screen, create sale | ✅ | ✅ | — | ✅ | — | `@pos_required` |
| Print receipt (own sale) | ✅ | ✅ | — | ✅ | — | `@pos_required` |
| Reprint receipt | ✅ | ✅ | — | — | — | `@admin_required` |
| Below-cost override (with reason) | ✅ | ✅ | — | — | — | `pos.services.confirm_sale` (`is_admin_user` + required reason) |
| Manual discount on sale | ✅ | ✅ | — | ✅ | — | `@pos_required` (unchanged in V6) |
| Sales history / sale detail | ✅ | ✅ | — | own only | ✅ | `@sales_history_required` |
| Cancel sale (with reason) | ✅ | ✅ | — | — | — | `@admin_required` |
| Promotions (list/create/edit) | ✅ | ✅ | — | — | — | `@admin_required` |
| Inventory summary, batch detail | ✅ | ✅ | ✅ | — | — | `@inventory_required` |
| Stock in (receive) | ✅ | ✅ | ✅ | — | — | `@inventory_required` |
| Barcode print | ✅ | ✅ | ✅ | — | — | `@inventory_required` |
| Product / promotion label print | ✅ | ✅ | ✅ | — | — | `@inventory_required` |
| Label templates (create/edit) | ✅ | ✅ | — | — | — | `@admin_required` |
| Catalog (products, categories, brands, suppliers, costs) | ✅ | ✅ | — | — | — | `@admin_required` |
| Batch upload | ✅ | ✅ | — | — | — | `@admin_required` |
| Quick-create (JSON API) | ✅ | ✅ | — | — | — | `can_manage_catalog` |
| Reports (view + CSV export) | ✅ | ✅ | — | — | ✅ | `@reports_required` |
| User management | ✅ | ✅* | — | — | — | `@users_required` |
| Assign/edit Owner role | ✅ | — | — | — | — | view logic |
| Store settings | ✅ | ✅ | — | — | — | `@settings_required` |
| Audit logs | ✅ | ✅ | — | — | — | `@audit_required` |
| Live logs / system health | ✅ | ✅ | — | — | — | `@system_required` |
| Data reset | ✅ (CLI only) | — | — | — | — | `reset_business_data` + `ALLOW_DATA_RESET` env |
| Django `/admin/` | superuser only | — | — | blocked | — | `is_staff` + `CashierAdminBlockMiddleware` |

\* Manager cannot modify Owners or superusers, cannot assign the Owner role,
cannot change own role or deactivate self. The last active Owner can never be
deactivated or demoted.

## Authentik group → role mapping (V6)

| Authentik group | StaffProfile role | Legacy Django group synced |
|---|---|---|
| `melodu-admin` | `OWNER` | `Admin` |
| `melodu-manager` | `MANAGER` | `Admin` |
| `melodu-inventory` | `INVENTORY` | — |
| `melodu-cashier` | `CASHIER` | `Cashier` |
| `melodu-report-viewer` | `VIEWER` | — |
| *(no melodu-\* group)* | no role → no access page | — |

If a user is in multiple `melodu-*` groups, the highest role wins
(Owner > Manager > Inventory > Cashier > Viewer). Local superusers are never
modified by sync.

## Design rules

- New views must use a capability decorator from `core/permissions.py` —
  never check role strings inline.
- New capabilities are functions (`can_<verb>_<noun>`) next to the existing ones,
  plus a `<noun>_required` decorator when a whole view is gated.
- Sensitive actions additionally require a typed reason and write an `AuditLog` row
  (see `docs/V6_PHASE_PLAN` Phase 5 list).
- Django model permissions (`user.has_perm`) are intentionally **not** used;
  do not mix the two systems.
