# Melodu POS — Permission Matrix (V4)

Five dashboard roles, stored on `accounts.StaffProfile.role`. Resolution order
(`core.permissions.get_user_role`):

1. Superuser → always **Owner** (cannot be locked out).
2. Explicit `StaffProfile` role.
3. Legacy group: `Admin` → Manager, `Cashier` → Cashier.
4. Otherwise → no dashboard access.

## Roles

| Role | Intended for |
| --- | --- |
| **Owner** | Store owner / super admin. Full access, including data reset (Phase 6). |
| **Manager** | Day-to-day manager. Everything except Owner-only maintenance. |
| **Inventory staff** | Stock-in, adjustments, expiry, label printing. |
| **Cashier** | POS sales and receipts only. |
| **Viewer / Auditor** | Read-only reports, sales history, audit. |

## Matrix

| Area | Owner | Manager | Inventory | Cashier | Viewer |
| --- | :---: | :---: | :---: | :---: | :---: |
| POS + receipts | ✓ | ✓ | – | ✓ | – |
| Products / catalog / costs | ✓ | ✓ | – | – | – |
| Stock-in / inventory / labels | ✓ | ✓ | ✓ | – | – |
| Promotions | ✓ | ✓ | – | – | – |
| Sales history | ✓ | ✓ | – | – | ✓ |
| Sale cancellation | ✓ | ✓ | – | – | – |
| Reports | ✓ | ✓ | – | – | ✓ |
| System health / live logs | ✓ | ✓ | – | – | – |
| Audit logs (read-only, V5) | ✓ | ✓ | – | – | – |
| User management | ✓ | ✓ | – | – | – |
| **Data reset (Phase 6)** | ✓ | – | – | – | – |

Notes:
- The dashboard landing page (`/dashboard/`) is open to every role.
- The scanner resolver API is open to every signed-in role (read-only metadata).
- Django Admin (`/admin/`) is separate and still requires `is_staff`; it is
  managed via Django Admin or the `set_user_role --django-admin` flag.

## Capability functions (`core.permissions`)

`can_manage_users`, `can_manage_catalog`, `can_manage_inventory`,
`can_manage_promotions`, `can_view_sales_history`, `can_cancel_sale`,
`can_view_reports`, `can_view_system`, `can_manage_settings`, `can_reset_data`.

Backward-compatible shims (unchanged behavior): `is_admin_user`
(Owner/Manager), `is_cashier_user`, `can_access_pos`.

## Owner-protection rules

- Only an Owner can assign the Owner role or edit an Owner/superuser.
- No user can change their own role or disable their own account.
- At least one active Owner must always remain.
