# V10-003 Store-level Permission Plan

Status: Complete
Last updated: 2026-06-16

## Purpose

Plan how future store-level authorization should extend the current role/capability system without changing current access behavior.

## Current Permission Model

| Item | Evidence | Status |
| --- | --- | --- |
| Effective role | `core.permissions.get_user_role()` resolves superuser, `StaffProfile`, then legacy groups. | Current |
| Built-in roles | Owner, Manager, Inventory, Cashier, Viewer. | Current |
| Capabilities | `core.capabilities.CAPABILITY_GROUPS` defines POS, sales, catalog, inventory, reports, and system capabilities. | Current |
| Per-user overrides | `StaffProfile.extra_capabilities` and `revoked_capabilities`. | Current |
| Cost visibility | `StoreSetting.cost_visible_roles`; Owner always sees costs. | Current |
| Store scoping | No store/user assignment exists. | Missing |

## Future Permission Shape

| Concept | Recommendation | Status |
| --- | --- | --- |
| Global Owner | Owner can see and manage all stores. | Future / Proposed |
| Store assignment | Add a user-to-store assignment model if multi-store is approved. | Future / Proposed |
| Store role | Keep capabilities, but evaluate them inside an assigned store context for store-scoped pages. | Future / Proposed |
| Cross-store manager | Allow assignment to more than one store instead of duplicating user accounts. | Future / Proposed |
| Store selector access | Only show stores the user can access. | Future / Proposed |
| System pages | Keep audit/log/system/settings owner/system-capability gated. | Future / Proposed |

## Candidate Model

Future implementation can consider a model similar to:

```text
StaffStoreAccess
- user
- store
- role or capability override scope
- is_default
- is_active
```

This is a planning note only. Do not create the model without a later implementation task and migration plan.

## Capability Impact

| Capability Area | Future Store Rule | Status |
| --- | --- | --- |
| `pos.access` | Can sell only from the selected/assigned store. | Future / Proposed |
| `inventory.manage` | Can receive/adjust/print only assigned-store inventory unless Owner/global manager. | Future / Proposed |
| `sales.view_history` | Can view sales for assigned stores only. | Future / Proposed |
| `sales.cancel` | Can cancel sales for assigned stores only. | Future / Proposed |
| `reports.view` | Can view assigned-store reports; Owner can aggregate. | Future / Proposed |
| `system.view_audit` | Needs explicit decision: all audit or assigned-store audit only. | Needs Verification |
| `system.manage_settings` | Needs explicit decision: global auth/system settings vs per-store settings. | Needs Verification |

## Test Requirements For Future Implementation

- Cashier cannot access another store's POS/session.
- Inventory staff cannot receive stock for unauthorized store.
- Manager cannot cancel a sale outside their store.
- Viewer/report user sees only allowed stores.
- Owner/superuser keeps all-store access.
- Legacy Admin/Cashier group fallback remains safe or is explicitly retired.

## Verification

Planning-only. Current permission code was inspected; no behavior changed.

