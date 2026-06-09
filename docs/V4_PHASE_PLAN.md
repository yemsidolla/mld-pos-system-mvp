# V4 Plan — Store Control, Product Classification, Printing & Admin Maintenance

V4 builds on the V3 baseline. It is delivered phase by phase; each phase is its
own branch/PR and is not started until the previous one is reviewed and
approved. No new runtime dependencies are planned across V4 (browser printing,
no ESC-POS library).

## Owner decisions (locked)

- **Roles** are stored on a custom `accounts.StaffProfile` model (not a swapped
  `AUTH_USER_MODEL`).
- **Map and keep**: existing `Admin`/`Cashier` Django groups keep working.
  Superusers are always Owner; legacy `Admin` maps to Manager and `Cashier` to
  Cashier when no profile exists.

## Phases

| # | Phase | Status |
| --- | --- | --- |
| 1 | User Management & Permissions | Implemented (this PR) |
| 2 | Product Classification (tags, animal type, life stage) | Planned |
| 3 | Printer Settings & 80mm Receipt | Planned |
| 4 | Label Template System | Planned |
| 5 | Promotion Label Printing | Planned |
| 6 | Safe Data Reset / Admin Maintenance | Planned |

Dependencies: 5 needs 4; 4 benefits from 2; 6 needs 1. Phases 1–3 are largely
independent.

---

## Phase 1 — User Management & Permissions (implemented)

**Goal:** Five explicit roles, dashboard user management, and matrix-based
gating before more powerful admin tools land.

**Roles:** Owner, Manager, Inventory staff, Cashier, Viewer/Auditor. See
`docs/PERMISSION_MATRIX.md`.

**Delivered**
- `accounts.StaffProfile(user, role)` + data migration backfilling existing
  users (superuser → Owner, `Admin` group → Manager, `Cashier` group → Cashier;
  unassigned users stay without access).
- `core.permissions` rewritten with role resolution (`get_user_role`),
  role/capability predicates, and capability decorators. `admin_required`,
  `pos_required`, `is_admin_user`, `is_cashier_user`, and `can_access_pos` keep
  their original behavior as compatibility shims.
- Dashboard user management at `/dashboard/users/` (list, create, edit, disable)
  for Owner/Manager. Role-aware navigation adds a **Users** link.
- Feature pages re-gated to the matrix: Inventory staff reach stock-in,
  inventory, and labels; Viewer reaches reports and sales history; Cashier is
  unchanged (POS + receipts).
- `set_user_role` extended to all five roles (legacy `admin`/`cashier` aliases
  retained); `setup_roles` seeds an Owner profile for the dev superuser.
- Audit logging for user create (`CREATE`), edit (`UPDATE`), role change
  (`ROLE_CHANGE`), and disable (`DEACTIVATE`).

**Protections**
- Only an Owner can assign the Owner role or edit an Owner/superuser account.
- A user cannot change their own role or disable their own account.
- At least one active Owner must always remain.
- Superusers are always treated as Owner so they can never be locked out.

**Non-goals (Phase 1):** custom `AUTH_USER_MODEL`, object-level permissions,
SSO/2FA, self-service password reset, in-dashboard `is_staff`/superuser toggles
(those stay in Django Admin / CLI).

**Tests:** role resolution & capability matrix, re-gated page access per role,
user create/edit/role-change auditing, Owner-only and last-Owner protections,
self-disable protection, `set_user_role` profile assignment. Full suite: 159
tests passing.

---

## Phases 2–6 (summaries)

The detailed 13-point plans (goal, scope, non-goals, affected files, data model,
migration, UI, permission, audit, tests, deployment, docs, risk/rollback) were
agreed with the owner and will be restated at the start of each phase branch.

- **Phase 2 — Product Classification:** flexible `ProductTag` (M2M) plus optional
  structured fields (animal type, life stage) on `Product`; product form,
  filters, search, and batch-upload columns; fully backward compatible.
- **Phase 3 — Printer Settings & 80mm Receipt:** singleton store/printer
  settings, de-hardcoded store info, a standalone thermal 80mm receipt template,
  browser print first, reprint permission + print audit.
- **Phase 4 — Label Template System:** `LabelTemplate` (paper size, orientation,
  field toggles); preset layouts (no drag-and-drop); batch printing + preview.
- **Phase 5 — Promotion Label Printing:** promotion labels (old/new price,
  discount, period) built on Phase 4 templates and the existing `Promotion`
  model.
- **Phase 6 — Safe Data Reset:** `reset_business_data` management command first
  (dry-run, exact-phrase confirm, env-flag guard, mandatory backup, audit
  before/after, Owner-only); dashboard UI only later if approved.
