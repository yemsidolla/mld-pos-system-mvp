# V5 Plan — Product Polish & UX Refinement

V5 builds on the V4 baseline. Its purpose is **polish and operational
efficiency, not new features**. It is delivered phase by phase; each phase is
its own branch/PR and is not started until the previous one is reviewed and
approved. No new runtime dependencies are planned. See `docs/V5_AUDIT.md` for
the findings these phases address.

## Working rules (unchanged from V4)

- Inspect the repository before changing anything; do not assume behavior.
- Keep the Django monolith. No redesign, no microservices, no framework change.
- No new dependencies unless clearly justified and approved.
- No new business requirements without owner decision.
- Protect sale logic and stock logic with tests; preserve existing behavior
  unless intentionally changed.
- Build phase by phase; verify each (`manage.py check` + full test suite +
  migrations) before moving on.

## Owner decisions (locked — approved 2026-06-10)

These were approved at audit sign-off. Any can be revisited before the relevant
phase begins.

- **Audit Log dashboard page**: Approved. Read-only page under Administration,
  Owner/Manager, reusing the existing `audit.AuditLog` model. No new model, no
  ability to edit/delete audit records.
- **Label print consolidation**: Differentiate by naming/role in early phases;
  keep both entry points for now (legacy single-batch "Barcode / QR Print" vs
  template-driven "Print Labels"). A full merge is deferred to a later, opt-in
  phase rather than removing a working tool mid-stream.
- **Terminology**: Adopt the recommended staff-facing renames (Reference Costs,
  System Health, Receive Stock, Stock Overview). Internal model/field names are
  unchanged; only user-facing labels move.
- **Pagination**: Approved to introduce in V5 (Phase 3) on the long lists.

## Phases

| # | Phase | Risk | Status |
| --- | --- | --- | --- |
| 1 | Dashboard & Navigation Polish (quick wins) | Low | Planned |
| 2 | Audit Log Dashboard (read-only) | Low–Med | Planned |
| 3 | List Consistency: search + pagination + status badges | Medium | Planned |
| 4 | Workflow Shortcuts: receive → print, label clarity | Medium | Planned |
| 5 | Shared CRUD list/form component (consistency hardening) | Medium | Planned |
| 6 | Mobile & Visual Polish (tables, icons, bottom nav) | Med–High | Future |

Dependencies: Phase 5 benefits from Phases 1 & 3 landing first. Phases 1–4 are
largely independent. Phase 6 is a future candidate, scoped after 1–5.

---

## Phase 1 — Dashboard & Navigation Polish

**Goal:** Remove the role-blind dead-ends and the worst naming ambiguities with
small, surgical changes.

**Scope**
- Make `dashboard_home_view` capability-aware (not `is_admin_user`-only):
  Inventory and Viewer roles see metrics and quick actions for areas they can
  actually open; remove the "Open POS"/POS card for roles excluded by
  `can_access_pos`.
- Apply approved renames in user-facing labels only (sidebar + page titles):
  Costs → Reference Costs, System → System Health, Stock-In → Receive Stock,
  Inventory (item) → Stock Overview.
- Add a Live Logs entry under Administration (or confirm removal with owner).
- Colored batch status badge using `get_status_display` in Inventory Summary.

**Non-goals:** new pages, permission-matrix changes, model/field renames.

**Tests:** home-page content per role (Owner/Manager/Inventory/Cashier/Viewer)
asserting no POS dead-end for Inventory/Viewer; nav label assertions; existing
suite stays green.

**Risk/rollback:** Low; template + context-processor changes, no migrations.

---

## Phase 2 — Audit Log Dashboard (read-only)

**Goal:** Surface the existing audit trail to Owner/Manager without Django Admin.

**Scope**
- Read-only list page under Administration with filters (action, module, user,
  date range) and a detail/expand for `old_value`/`new_value`.
- `reports_required`-style gating using a new/existing capability
  (`can_view_system` or a dedicated `can_view_audit`); strictly read-only.
- Pagination from the start (aligns with Phase 3).

**Non-goals:** editing/deleting audit entries; new audit action types; export
(could be a later add-on).

**Tests:** access per role; filter correctness; read-only enforcement (no
create/update/delete routes); pagination.

**Risk/rollback:** Low–Med; additive view + template + URL, no model changes.

---

## Phase 3 — List Consistency: search, pagination, status

**Goal:** One predictable list experience across the app.

**Scope**
- Standardize on **server-side filtering** for list screens; reconcile Inventory
  Summary (currently client-side JS filter) and the bespoke search fields.
- Add pagination to Products, Sales History, Inventory batches, Stock Movement
  report (and the new Audit Log page).
- Consistent status-badge coloring + `get_*_display` usage across tables.
- Consistent Reset button + filter layout on every filtered list.

**Non-goals:** changing what each list queries; new columns/data.

**Tests:** pagination boundaries; filter persistence across pages; performance
sanity on large datasets; sale/stock logic untouched (regression check).

**Risk/rollback:** Medium; view-layer changes — guard with tests for unchanged
result sets.

---

## Phase 4 — Workflow Shortcuts & Label Clarity

**Goal:** Cut repeated steps in the receive→print and label journeys.

**Scope**
- "Print label" shortcut from the Stock-In success state and Batch Detail that
  carries the batch into Print Labels (no re-selection).
- Clarify the two label entry points by naming/role (per locked decision):
  legacy quick single-batch barcode vs template-driven Print Labels; add
  cross-links so users don't hunt across Catalog/Inventory groups.
- Optional: lateral links between related reports (Low Stock ↔ Expiry ↔ Stock
  Summary).

**Non-goals:** merging/removing a label feature (deferred); new label fields.

**Tests:** shortcut pre-selects the correct batch; audit (`BARCODE_PRINT`) still
fires; access unchanged.

**Risk/rollback:** Medium; mostly template/links + a query-param pass-through.

---

## Phase 5 — Shared CRUD List/Form Component

**Goal:** Lock in consistency for the six near-identical management screens.

**Scope**
- Extract a shared list template + form template (header actions, filter block,
  Reset, table shell, empty state) reused by Products, Categories, Brands,
  Suppliers, Reference Costs, Promotions, Label Templates.
- No behavior change — pure refactor to a single source of truth.

**Non-goals:** changing fields, validation, or permissions.

**Tests:** each screen renders identically (snapshot-style assertions on key
elements); full suite green.

**Risk/rollback:** Medium; template refactor — land behind tests, revertible.

---

## Phase 6 — Mobile & Visual Polish (future)

**Goal:** Improve phone/tablet ergonomics once 1–5 are stable.

**Candidate scope (to be detailed):**
- Stacked/card layout for wide tables on phones.
- Lightweight icon set for sidebar + a role-weighted mobile bottom nav (not
  first-5).
- Cost-terminology rationalization with inline help (Reference / List /
  Actual-landed).
- Optional unified "Labels" hub.

**Status:** Future — scoped after Phase 5 review.

---

## Verification expectations (every phase)

- `manage.py check` clean; `manage.py check --deploy` introduces no new warnings.
- Full test suite passes (currently 190 tests); new tests added per phase.
- Migrations (if any) are additive/safe with reverse operations.
- `docs/TASKS.md` and `docs/DEVELOPMENT_LOG.md` updated; compose service list
  remains `postgres` + `web` only.
