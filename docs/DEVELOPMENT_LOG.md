# Development Log

## 2026-08-04

### Infra: Replace MinIO with Garage for S3 media

- Replaced Compose `minio` / `minio-init` with a single-node `garage` service
  pinned to `dxflrs/garage:v2.3.0` (stable tag verified on Docker Hub /
  Deuxfleurs releases).
- Added `docker/garage/garage.toml` (`replication_factor = 1`, S3 `:3900`,
  admin/RPC on container loopback only).
- Added `scripts/bootstrap_garage.sh` (layout assign/apply, bucket create, key
  import from `S3_*` env, bucket allow) and `scripts/migrate_minio_to_garage.sh`
  (key-preserving object copy with count/bytes verification).
- Renamed MinIO backup/restore scripts to `backup_garage.sh` /
  `restore_garage.sh`; kept `data/minio` for rollback (not deleted).
- `.env.example` and settings default endpoint now point at Garage; all `S3_*`
  variable names unchanged. No Django model/view/migration changes.
- Docs: `MINIO_STORAGE_GUIDE.md` → `GARAGE_STORAGE_GUIDE.md`; updated deployment,
  backup, README architecture line, and current status.

## 2026-06-17

### Product Documentation Foundation Rebuild

- Rebuilt `docs/product/` foundation to numbered sequence 00–11 per Standard Way
  of Working: system map, vision, governance, UX rules, module map, BRD, PRD,
  TRD, roadmap, backlog, QA/release, documentation map.
- Created `02_TEAM_GOVERNANCE_AND_DELIVERY_RULES.md` and
  `03_DESIGN_SYSTEM_AND_UX_RULES.md`.
- Added version PRD/TRD files for V6–V10; renamed scope and release note files.
- Renumbered ADRs 0002/0003 and 0005/0006 to match foundation doc order.

### V1–V5 Historical Version Documentation Rebuild

- Created `docs/versions/v1/` through `docs/versions/v5/` with scope, as-built,
  tasks, QA checklist, and release note for each historical version.
- Updated version roadmap, documentation map, and implementation backlog with
  carry-forward items for V6–V10.
- Legacy phase docs in `docs/legacy/` retained as supporting evidence (Duplicate
  / Overlapping).
- Documentation-only; no application behavior changed.

### Product Foundation Docs Verified Against Codebase

- Updated `docs/product/00_CURRENT_SYSTEM_MAP.md` with codebase-verified routes,
  capability gates, capability registry, test counts, and corrected receipt path.
- Updated `docs/product/04_MODULE_MAP.md`, `04_PRD.md`, `05_TRD.md`, and
  `07_IMPLEMENTATION_BACKLOG.md` to match current implementation.
- Documented known gap: `Sale.Status.REFUNDED` exists in models but no refund
  workflow is implemented.

### Docs Folder Physical Reorganization

- Moved guides to `docs/guides/`, runbooks/checklists to `docs/operations/`,
  reference docs to `docs/reference/`, V2–V5 phase docs to `docs/legacy/`,
  and V6 auth docs into `docs/versions/v6/`.
- `docs/` root now holds only foundation docs: README, STANDARD_WAY_OF_WORKING,
  DESIGN_SYSTEM, CURRENT_STATUS, TASKS, DEVELOPMENT_LOG.
- Updated cross-references across the repo and rewrote folder indexes.
- Added README indexes under `guides/`, `operations/`, `reference/`, and
  `legacy/`.

### Docs Folder Organization Index

- Added `docs/README.md` as the docs folder entry point with folder layout,
  subfolder indexes, guide/checklist catalogs, legacy doc list, and placement
  rules aligned with `docs/STANDARD_WAY_OF_WORKING.md`.
- Added lightweight indexes under `docs/product/`, `docs/versions/`, and
  `docs/decisions/`.
- Updated `docs/product/11_DOCUMENTATION_MAP.md`, `docs/CURRENT_STATUS.md`, and
  `README.md` to point to the new docs index.

## 2026-06-16

### V8-001 Inventory Workflow Audit

- Started V8 Inventory, Label, and Promotion Professionalization.
- Audited inventory stock-in, stock overview, batch detail, adjustment, damage,
  expiry, maintenance expiry, reports, movement ledger, audit, and permission
  flows.
- Confirmed stock-changing services remain transaction-protected and
  movement/audit-backed.
- Added `docs/versions/v8/V8_INVENTORY_WORKFLOW_AUDIT.md` and mapped operational
  visibility follow-ups to V8-002 through V8-010.

### V8-002 Stock Batch Visibility Polish

- Improved stock overview batch rows with supplier, receiver/date, expiry state,
  days to expiry, received/available quantities, price/cost-safe display, codes,
  and print shortcut.
- Improved batch detail with received/available metrics, original barcode,
  receiving history, barcode/QR generation status, and latest movement preview.
- Added a report-permission context flag so the movement report shortcut is only
  shown to users who can open reports.
- Added focused inventory tests for visible context and hidden-cost behavior.

### V8-003 Expiry And Low-Stock Flow Polish

- Added reorder gap and stock state context to stock overview, stock summary, and
  low-stock report pages.
- Added Receive Stock/Open Stock actions to move staff from low-stock reports
  into inventory workflows.
- Added supplier, days-to-expiry, recommended action, and Open Batch link to the
  expiry report.
- Verified inventory and report behavior with 26 focused tests.

### V8-004 Cost Visibility Review

- Added cost visibility enforcement to stock-in because the page exposes actual
  and landed batch cost fields.
- Clarified product default cost, supplier reference unit cost, stock-in actual
  unit cost, and landed unit cost wording.
- Added product default cost and notes to the reference cost list for manager
  comparison.
- Updated business rules and verified catalog, inventory, and cost visibility
  behavior with focused tests.

### V8-005 Barcode And QR Workflow Polish

- Added barcode/QR print guidance explaining exact batch selection with Melodu
  custom codes versus original product barcode selection.
- Added selected-batch confirmation before printing quick barcode/QR labels,
  including generated barcode and QR image status.
- Added scanner modal quality guidance for camera, uploaded image, and manual
  fallback workflows.
- Verified barcode print, scanner placement, and scan resolver behavior with 14
  focused tests.

### V8-006 Label Template Management Polish

- Added label template list metrics, orientation/font context, and enabled field
  summaries.
- Grouped the label template form into identity, paper/text, fields, custom
  text, and default/status sections.
- Added display-only `enabled_field_labels` and clearer form help text for
  paper, barcode/QR, default, and active behavior.
- Updated the label template guide and verified the label test suite.

### V8-007 Label Print Workflow Polish

- Added product/shelf label setup guidance and no-print preview summaries for
  template type, selected batch count, copies per batch, and total labels.
- Added promotion label setup guidance and no-print preview summaries for active
  product count, copies per product, total labels, and promotion window.
- Added explicit Open Print Dialog controls to preview sections.
- Updated the label template guide and verified the label test suite.

### V8-008 Promotion Lifecycle Polish

- Added promotion lifecycle metrics, timeline details, human discount labels,
  scope labels, and below-cost status badges to the promotion list.
- Grouped promotion form fields into identity, discount/dates, scope, and safety
  sections.
- Added validation that dashboard promotions choose either one product or one
  category, not both.
- Updated promotion business rules and verified promotion dashboard tests.

### V8-009 POS Promotion Safety Polish

- Added POS cart promotion discount summary and was/now/save line-item
  explanation.
- Added cashier-facing manager approval warning for below-cost cart lines.
- Added admin-facing reminder that below-cost checkout requires an override
  reason and a warning for promotions explicitly allowed below cost.
- Verified POS page, service pricing, and payment flow tests.

### V8-010 Inventory Traceability Review

- Added movement report search by product, batch, custom code, reference, note,
  or user and a movement type filter.
- Added batch custom code, movement note, product code, and gated batch detail
  links to the stock movement report.
- Added gated Inventory Audit Logs shortcut for users who can view audit logs.
- Documented trace paths for stock-in, sale, cancellation, adjustment, damage,
  and expiry workflows.
- Verified report and audit dashboard tests.

### Controlled Foundation Reset Documentation

- Added the preferred product documentation foundation under `docs/product/`:
  current system map, product vision/operating model, module map, BRD, PRD,
  TRD, version roadmap, implementation backlog, QA/release process, and
  documentation map.
- Added V6 reset documents under `docs/versions/v6/`: scope, as-built review,
  task tracker, QA checklist, and release note draft.
- Added ADR-0001 through ADR-0007 under `docs/decisions/` for the Django
  monolith, batch-level inventory, Authentik/OIDC, role/capability
  authorization, dashboard design system, label template strategy, and standard
  way of working.
- Updated README, current status, and task tracker to point future AI/human
  work toward the new authoritative maps while keeping older docs as supporting
  references.
- No application behavior, source code, routes, models, migrations,
  permissions, templates, CSS, reset scripts, or design-system rules changed.

### V7-V10 Version Planning And Completion Tracker

- Added V7-V10 version planning documents under `docs/versions/` following the
  Standard Way of Working: scope, task checklist, QA checklist, and release note
  draft for each planned version.
- Added `docs/versions/VERSION_COMPLETION_TRACKER.md` as the durable checklist:
  completed tasks should be marked `Complete` and kept in place rather than
  deleted, with evidence recorded for future AI/human contributors.
- Aligned the product roadmap and implementation backlog to the V7-V10 version
  sequence: V7 UX/UI cleanup, V8 inventory/label/promotion professionalization,
  V9 reports/audit/owner control, and V10 multi-store/scale-readiness
  foundation.

### V7-001 Navigation And Naming Cleanup

- Completed the V7-001 navigation audit and recorded it in
  `docs/versions/v7/V7_NAVIGATION_AUDIT.md`.
- Standardized low-risk administration labels: `Settings` to `Store Settings`,
  `Login & Auth` to `Login & Authentication`, and `Styleguide` to
  `Style Guide`.
- Added dashboard shell assertions for the cleaned labels.
- Verified: `manage.py check` clean; targeted dashboard/navigation/auth/
  styleguide tests passing.

### V7-002 Dashboard Home Polish

- Standardized the POS quick action wording from `POS Sale` to `Open POS`.
- Added role-safe dashboard home shortcuts for `Print Labels` and `Batch Upload`
  behind existing inventory/catalog capabilities.
- Updated dashboard home tests to protect Inventory and Cashier shortcut
  visibility.
- Verified: `manage.py check` clean; targeted dashboard shell/home tests
  passing.

### V7-003 POS Cashier Workflow Polish

- Fixed POS quick-key buttons so they submit product original barcodes, matching
  the existing POS scan rules for original barcode or Melodu custom code.
- Hid hand-picked, top-seller, and promotion quick keys for products without an
  original barcode so cashiers do not see unusable quick actions.
- Added quick-key regression tests for barcode-backed buttons and no-barcode
  product hiding.
- Verified: `manage.py check` clean; targeted POS/scanner tests passing; full
  POS app test suite passing.

### V7-004 Catalog/Product List Polish

- Added a visible product search row above the product table with search,
  scanner, and reset actions while keeping existing column filters.
- Kept the Photo column and added a product-image render test so uploaded
  product pictures remain visible in the catalog table.
- Wrapped the product table in the shared horizontal table scroller and upgraded
  the empty result state with a clear create-product action.
- Corrected V7 navigation/styleguide test expectations for escaped ampersands
  and the `Living Style Guide` title.
- Verified against the mounted working tree: `manage.py check` clean; 19
  catalog-focused tests passing; 55 V7 regression tests passing.

### V7-005 Inventory And Stock Receiving Workflow Polish

- Added staff-facing help text to stock-in fields for product barcode
  requirements, supplier selection, batch quantity, expiry, actual/landed cost,
  selling price, and receiving notes.
- Added a `Receive Another Batch` shortcut after successful stock-in.
- Clarified inventory lookup copy and added a `Level` column so low-stock
  product summaries are visible without opening reports.
- Added an `Open` action to batch rows and clearer guidance/errors on batch
  adjustment, damage, and expiry forms.
- Verified against the mounted working tree: `manage.py check` clean; 23
  inventory tests passing; 78 V7 regression tests passing.

### V7-006 Promotion And Label Page Polish

- Added promotion label workflow links from promotion and label template pages.
- Added a promotion timeline column for running, upcoming, ended, and inactive
  promotions.
- Added promotion form guidance for no-stacking behavior, discount values,
  product/category scope, and below-cost risk.
- Added scanner batch lookup to template-based `Print Labels` and help text to
  product/promotion label print forms.
- Verified against the mounted working tree: `manage.py check` clean; 18
  promotion/label focused tests passing; 93 V7 regression tests passing.

### V7-007 Reports Page Readability Polish

- Added metric summaries to stock summary, low stock, expiry, stock movement,
  and staff sales reports without changing report inclusion rules.
- Added lateral links from daily sales/staff sales/stock movement reports and
  action links from low-stock and expiry rows.
- Added table scroll wrappers, stock level badges, expiry severity badges, and
  batch detail links for denser report pages.
- Verified against the mounted working tree: `manage.py check` clean; 11
  reports tests passing; 104 V7 regression tests passing.

## 2026-06-10

### V5 Phase 6: Mobile & Visual Polish

- Replaced the mobile bottom nav's "first five sidebar items" with a curated,
  role-weighted set (Dashboard → POS → Stock Overview → Products → Sales History
  → Reports → Receive Stock, capped at 5), built from the same capability flags
  so it always matches access. Cashiers get Dashboard + POS; Owners get the five
  highest-value destinations instead of Categories/Brands.
- Added a mobile table affordance: touch-momentum horizontal scrolling and
  denser cell padding on small screens; pagination controls space out on phones.
- Added cost-terminology help inline on Receive Stock (Actual vs Landed unit
  cost) and Reference Costs (expected vendor cost vs price paid per batch).
- Deferred (documented in `docs/legacy/V5_PHASE_PLAN.md`): full stacked-card tables and
  a graphical icon set — high template churn for low risk-adjusted benefit;
  smooth horizontal scroll is the interim.
- Verified: `manage.py check` clean; full suite 203 tests passing (was 202);
  no migrations.

### V5 Phase 5: Shared List Filter & Consistency Hardening

- Extracted a shared `dashboard/_list_filter.html` partial (filter grid +
  consistent Filter + Reset) and adopted it on the field-loop filter lists:
  master-data (Categories/Brands/Suppliers), Sales History, and Audit Logs.
- Closed the Reset-button gaps: Sales History and the Daily Sales report now
  offer Reset like every other filtered list. Standardized the Daily Sales
  status/payment cells onto display labels.
- Assessed and deferred a single generic CRUD template for all list/form
  screens: the master-data trio already shares one template, while Products,
  Reference Costs, Promotions, and Label Templates have genuinely different
  columns and controls (e.g. the product scan button). Collapsing them would
  add risk for little benefit, so the shared filter partial captures the real
  duplication instead. See `docs/legacy/V5_PHASE_PLAN.md`.
- Verified: `manage.py check` clean; full suite 202 tests passing; no migrations.

### V5 Phase 4: Workflow Shortcuts & Label Clarity

- After receiving stock, the Receive Stock page now shows a "Batch Received"
  panel with one-click "Print Barcode / QR", "Print Template Label", and "View
  Batch" actions (via a `?created=<id>` redirect param) — removing the old
  re-selection round-trip. The Batch Detail page gained the same print
  shortcuts for active batches.
- `Barcode / QR Print` and `Print Labels` now accept `?batch=<id>` to
  pre-select the batch (and, for Print Labels, the default product template),
  so the shortcuts land ready to print.
- Clarified the two label entry points: each page now explains its role
  (quick single-batch barcode vs template-driven multi-batch) and cross-links
  to the other plus Label Templates.
- Added lateral links between the related stock reports (Low Stock, Expiry,
  Stock Summary). Switched the Batch Detail status to its display label.
- Verified: `manage.py check` clean; full suite 202 tests passing (was 199);
  no migrations.

### V5 Phase 3: List Consistency (search, pagination, status)

- Added a shared `core.pagination.paginate` helper and a reusable
  `dashboard/_pagination.html` partial. Applied pagination to Products (25),
  Sales History (25), Stock Movement report (50), Stock Overview batches (25),
  and the Audit Log page (refactored onto the shared helper). The Stock Movement
  report no longer hard-caps at 300 rows.
- Converted Stock Overview search from client-side JS row filtering to a
  server-side `q` query (matches product name/code/barcode, batch number, and
  custom code) — the last page using the ad-hoc `data-table-filter` pattern.
- Standardized status rendering on human-readable display labels: colored batch
  status badge (already added in Phase 1) plus movement-type display label in
  the Stock Movement report ("Sale" instead of "SALE").
- Verified: `manage.py check` clean; full suite 199 tests passing (was 197);
  no migrations.

### V5 Phase 2: Audit Log Dashboard (read-only)

- Added a read-only Audit Logs page (`/dashboard/audit-logs/`) under
  Administration for Owner/Manager, surfacing the existing `audit.AuditLog`
  trail without requiring Django Admin access. New capability `can_view_audit`
  and `audit_required` decorator.
- Filters by action, module, user, and date range; paginated 25 per page
  (introduces the shared pagination control reused in Phase 3). Old/new value
  detail is shown in an expandable row.
- Strictly read-only: no create/update/delete routes; a POST writes nothing.
- Verified: `manage.py check` clean; full suite 197 tests passing (was 193);
  no migrations.

### V5 Phase 1: Dashboard & Navigation Polish

- Made `dashboard_home_view` capability-aware instead of `is_admin_user`-only.
  Inventory staff and Viewers no longer see POS shortcuts they cannot use (the
  home page previously offered them an "Open POS" button and "POS Sale" card
  that dead-ended at a 403). Each role now lands on metrics and quick actions
  for areas it can actually open.
- Applied the approved staff-facing renames in nav labels and page titles:
  "Costs" → "Reference Costs", "System" → "System Health", "Stock-In" →
  "Receive Stock", "Inventory" (item) → "Stock Overview". Model/field names are
  unchanged.
- Added a "Live Logs" entry under Administration (previously reachable only by
  URL); gated by the same `can_view_system` capability as System Health.
- Colored the batch status badge in Stock Overview and switched to
  `get_status_display` (was a plain, uncolored raw enum value).
- Verified: `manage.py check` clean; full suite 193 tests passing (was 190);
  no migrations.

### Dashboard Sidebar Navigation Grouping

- Restructured the dashboard sidebar (`app/templates/dashboard/base.html`) into
  a header / scrollable body / footer layout: brand stays pinned at the top,
  the Django Admin link and version stay pinned at the bottom, and the
  navigation list scrolls independently when it overflows the viewport.
- Grouped sidebar navigation by functional area in
  `core.context_processors.dashboard_context` (new `dashboard_nav_groups`):
  Overview, Sales, Catalog, Inventory, Reports, Administration. The flat
  `dashboard_nav_items` list (used by the mobile bottom nav) is now derived
  from the grouped list, preserving its existing order.
- Renamed the "Labels" nav entry to "Barcode / QR Print" (matches its existing
  page title) to disambiguate it from "Print Labels", "Promotion Labels", and
  "Label Templates" now that they sit in the same group.
- Added `.sidebar-header`, `.sidebar-body` (scrollable, thin scrollbar), and
  `.nav-group`/`.nav-group-title` styles to `dashboard.css`. No new
  dependencies; mobile bottom nav and print styles unchanged.
- Verified: full suite 190 tests passing; rendered sidebar markup checked via
  Django test client for an Owner/superuser session.

## 2026-06-09

### V4 Phase 6: Safe Data Reset / Admin Maintenance

- Added the `reset_business_data` management command (Owner-level, CLI only) to
  safely clear business data with scopes: sales, movements, batches, demo,
  catalog, all. Deletions run in a single transaction in foreign-key-safe order.
- Layered safety: dry run by default; execution requires `ALLOW_DATA_RESET=1`,
  the exact phrase `RESET <scope>`, and `--backup-confirmed`. A `DATA_RESET`
  audit entry is written before and after. Users, roles, store settings, label
  templates, and audit logs are never deleted.
- No dashboard UI (intentional); documented in `docs/operations/RESET_ADMIN_RUNBOOK.md`.
- Verified: `manage.py check` clean; full suite 190 tests passing (was 184);
  migrations apply cleanly.

### V4 Phase 5: Promotion Label Printing

- Added a Promotion Labels page (`/dashboard/labels/promotions/`, Owner/Manager/
  Inventory) that resolves a promotion's products (product or category scope),
  computes the promo price for each with the shared `calculate_promotion_price`,
  and prints special-offer labels showing the old price, new price, savings, and
  promotion period using a Promotion/Custom label template.
- Seeded a default 70×50mm promotion label template via migration; printing is
  audited as `BARCODE_PRINT` with the promotion reference, template, and product
  codes. Added a Promotion Labels nav item.
- Documented in `docs/guides/PROMOTION_LABEL_GUIDE.md`.
- Verified: `manage.py check` clean; full suite 184 tests passing (was 182);
  migrations apply cleanly.

### V4 Phase 4: Label Template System

- Added a new `labels` app with `LabelTemplate` (type, paper size, orientation,
  font size, per-field show/hide toggles, header/footer, one default per type).
  A data migration seeds a default 50×30mm product template.
- Owner/Manager manage templates at `/dashboard/labels/templates/` (audited
  create/update); Owner/Manager/Inventory print at `/dashboard/labels/print/` by
  choosing a template, active stock batches, and a per-batch quantity, with a
  live preview and browser print. Printing records a `BARCODE_PRINT` audit.
- Labels read from stock batches (barcode/QR, price, expiry, batch) and products
  (name, SKU, animal type, life stage) plus the store name/logo; only the fields
  enabled on the template render. Added Label Templates and Print Labels nav.
- The legacy single-batch label page (`/dashboard/barcode-print/`) is unchanged.
- Documented in `docs/guides/LABEL_TEMPLATE_GUIDE.md`.
- Verified: `manage.py check` clean; full suite 182 tests passing (was 175);
  migrations apply cleanly.

### V4 Phase 3: Printer Settings & 80mm Receipt

- Added the `core.StoreSetting` singleton (store identity plus receipt/printer
  configuration), defaulting receipts to 80mm; exposed it through an
  Owner/Manager Settings page (`/dashboard/settings/`) and Django Admin (single,
  non-deletable row). Settings edits are audited as `SETTING_CHANGE`.
- Replaced the dashboard-chrome receipt with a standalone thermal receipt
  template whose width, font size, store name/address/phone/logo, header, and
  footer come from the settings; dashboard labels now use the configured store
  name instead of a hardcoded value.
- Added an audited `RECEIPT_PRINT` reprint action from the sale detail page
  (Owner/Manager), and a Settings navigation link.
- Browser printing remains the supported path (no ESC-POS dependency).
- Documented in `docs/guides/PRINTER_RECEIPT_GUIDE.md`.
- Verified: `manage.py check` clean; full suite 175 tests passing (was 167);
  migrations apply cleanly.

### V4 Phase 2: Product Classification

- Added `catalog.ProductTag` (flexible tags) and optional `animal_type` and
  `life_stage` choice fields on `Product`; all classification is optional so
  existing products stay valid.
- Extended the product form with classification dropdowns and a tag picker;
  added product-list filters for animal type, life stage, and tag, with the
  free-text search also matching tag names and a new Classification column.
- Updated Django Admin with the new filters, a tag picker, and a `ProductTag`
  section; product audit snapshots now record the tag list (m2m-aware).
- Added optional batch-upload columns `animal_type`, `life_stage`, and `tags`
  (auto-creates tags, validates choices, replaces tags only when provided);
  files without these columns still upload. Updated the products CSV template.
- Documented in `docs/guides/PRODUCT_CLASSIFICATION_GUIDE.md` and the batch-upload
  guide.
- Verified: `manage.py check` clean; full suite 167 tests passing (was 159);
  migration applies cleanly.

### V4 Phase 1: User Management & Permissions

- Added `accounts.StaffProfile` (Owner, Manager, Inventory staff, Cashier,
  Viewer) with a data migration that backfills existing users (superuser →
  Owner, `Admin` group → Manager, `Cashier` group → Cashier) and leaves
  unassigned users without dashboard access.
- Rewrote `core.permissions` with `get_user_role` resolution (superusers are
  always Owner), role/capability predicates, and capability decorators.
  `admin_required`, `pos_required`, `is_admin_user`, `is_cashier_user`, and
  `can_access_pos` are preserved as compatibility shims (map and keep).
- Added dashboard user management at `/dashboard/users/` (list, create, edit,
  disable) for Owner/Manager, with role-aware navigation and a Users link.
- Re-gated inventory, labels, reports, and sales-history pages to the new
  permission matrix; Cashier access (POS + receipts) is unchanged.
- Extended `set_user_role` to all five roles (legacy `admin`/`cashier` aliases
  retained) and made `setup_roles` seed an Owner profile for the dev superuser.
- Added Owner-only assignment, self-protection, and last-Owner safeguards, plus
  audit logging for user create, update, role change, and disable.
- Documented the plan and matrix in `docs/legacy/V4_PHASE_PLAN.md` and
  `docs/reference/PERMISSION_MATRIX.md`; updated `docs/guides/USER_MANAGEMENT_GUIDE.md`.
- Verified: `manage.py check` clean; full suite 159 tests passing (was 141);
  migrations apply cleanly; `check --deploy` shows only the pre-existing
  environment warnings.

## 2026-06-06

### Phase 0: Project Bootstrap

- Created the Django monolith project under `app/`.
- Added Docker Compose services for PostgreSQL and web.
- Added `/health/`, static/media/log/database persistence folders, and starter documentation.
- Verified Docker startup, Django migrations, collectstatic, admin login redirect, health check, and restart persistence.
- Documented host-level reverse proxy expectations for production.

### Phase 1: Master Data

- Added catalog models: `Category`, `Brand`, `Supplier`, and `Product`.
- Added admin registration with search and filters for master data management.
- Added product barcode uniqueness behavior and active/inactive status visibility.
- Added `Pillow` for product image support.
- Added tests for barcode uniqueness, blank barcode support, admin search/filter configuration, and health URL.
- Applied `catalog.0001_initial` migration.
- Set the local admin account to username `admin` with the provided password for development verification.

### Phase 2: Audit Foundation

- Added `AuditLog` with action choices from the approved project plan.
- Added `create_audit_log()` helper plus request IP and user-agent capture utilities.
- Added Django auth signal handlers for login success and login failure.
- Registered `AuditLog` in Django Admin as read-only and non-deletable.
- Added tests for the audit helper, forwarded IP parsing, read-only admin behavior, and login signals.
- Applied `audit.0001_initial` migration.

### Phase 3: Stock-In and Batch

- Added `StockBatch` and `InventoryMovement`.
- Added stock batch status choices: active, sold out, expired, damaged, and locked.
- Added `receive_stock()` service using a database transaction.
- Added batch number generation using `BYYNNNN`.
- Added Melodu custom code generation using the approved barcode standard.
- Added Code128 barcode and QR PNG generation.
- Added a staff-only stock-in page at `/dashboard/stock-in/`.
- Registered stock batches and inventory movements in Django Admin as generated records.
- Added tests for custom code generation, stock-in creation, image generation, movement/audit creation, invalid product handling, and page access.
- Applied `inventory.0001_initial` migration.

### Phase 4: Barcode / QR Print

- Added a staff-only barcode/QR label page at `/dashboard/barcode-print/`.
- Added label selection by active stock batch and label quantity.
- Added print-friendly label markup with product, price, expiry, batch number, barcode, QR code, and custom code.
- Added `BARCODE_PRINT` audit logging when a print action is recorded.
- Added tests for label preview fields and print audit creation.

### Phase 5: POS Sale

- Added `Sale` and `SaleItem` models.
- Added POS scan service for original barcode and Melodu custom code behavior.
- Added strict Melodu custom code parsing and validation.
- Added transaction-protected sale confirmation.
- Added stock deduction from exact stock batches and automatic `SOLD_OUT` status when quantity reaches zero.
- Added sale inventory movement and `SALE_CREATE` audit logging.
- Added staff-only POS page at `/dashboard/pos/`.
- Added receipt page at `/dashboard/pos/receipt/<sale_id>/`.
- Added tests for custom code parsing, original barcode batch selection, exact custom-code batch lookup, expired stock blocking, stock deduction, non-negative stock, required sale item batch link, and page access.
- Applied `pos.0001_initial` migration.

### Phase 6: Sales History and Cancellation

- Added sales history page with date, cashier, and payment method filters.
- Added sale detail page with sale items and cancellation form.
- Added `cancel_sale()` service using a database transaction.
- Added stock reversal to the original stock batch.
- Added `RETURN` inventory movement creation for cancellations.
- Added `SALE_CANCEL` audit logging.
- Restricted cancellation routes to superusers.
- Added tests for stock reversal, required cancellation reason, history/detail visibility, and cashier cancellation denial.

### Phase 7: Inventory Adjustment and Expiry Control

- Added inventory summary page with product stock summary and batch detail links.
- Added batch detail page with adjustment, damage, and expired-stock forms.
- Added expiry status helper with Expired, Critical, Warning, and Normal states.
- Added `adjust_stock()`, `mark_batch_damaged()`, and `mark_batch_expired()` services.
- Ensured adjustments require reasons and cannot make quantity negative.
- Added inventory movement and audit creation for adjustment, damaged, and expired stock actions.
- Restricted inventory pages to superusers.
- Added tests for adjustment, required reason, negative prevention, expiry status, damaged stock, expired stock, and page permissions.

### Phase 8: Reports

- Added reports index and six basic report pages.
- Added daily sales totals and sale list.
- Added stock summary and low-stock reports.
- Added expiry report using the existing expiry status helper.
- Added stock movement trace report.
- Added staff sales aggregation by cashier.
- Restricted report pages to superusers.
- Added tests for all report pages and cashier access denial.

### Phase 9: Live Backend Logs and System Health

- Added live backend log viewer at `/dashboard/live-logs/`.
- Added 5-second auto refresh for the log viewer.
- Added log redaction for secret-like values.
- Added system health page at `/dashboard/system-health/`.
- Added database, disk, log writable, last sale, last stock-in, and last error checks.
- Set `APP_VERSION` and Docker `DATA_ROOT=/vol`.
- Added tests for log ordering, redaction, admin access, cashier denial, and health output.

### Phase 10: Permission and Security

- Added shared role helpers and decorators in `core.permissions`.
- Added default role creation for `Admin` and `Cashier` groups.
- Added `setup_roles` management command.
- Changed POS access to allow Admin or Cashier roles.
- Changed stock-in, barcode print, inventory, reports, sales history/cancellation, live logs, and system health to Admin-only.
- Added middleware to block Cashier users from Django Admin even if they are marked staff.
- Added secure cookie and frame options defaults.
- Added tests for role creation, Admin/Cashier checks, POS-only cashier access, and Django Admin blocking.

### Phase 11: Production Deployment and Backup

- Added `docker-compose.prod.yml` with production restart policies for PostgreSQL and Django.
- Updated `.env.example` with app version and production security fields.
- Added backup and restore scripts under `scripts/`.
- Added `docs/guides/BACKUP_GUIDE.md`.
- Added `docs/operations/PRODUCTION_CHECKLIST.md`.
- Expanded `docs/guides/DEPLOYMENT_GUIDE.md` with VPS deployment, role setup, backup, and restore steps.
- Updated README with current MVP status and operational links.
- Verified production Compose config with `.env.example`.
- Ran database and media backup scripts successfully against the local stack.

## 2026-06-08

### V1 Stabilization

- Removed the internal Docker Nginx service and Docker Nginx config.
- Kept production reverse proxy responsibility with host-installed Nginx.
- Added `docker-compose.local.yml` for local/iPhone testing with Django published directly on port 8000.
- Added dashboard management pages for categories, brands, and suppliers.
- Tightened POS cart quantity handling and added cart update/remove controls.

### Batch Upload Feature

- Added the `batch_upload` Django app.
- Added `BatchUploadJob` and `BatchUploadRow` staging models.
- Added CSV and XLSX parsing with strict schema headers per upload target.
- Added downloadable CSV templates for categories, brands, suppliers, products, and stock-in.
- Added admin-only `/dashboard/batch-upload/` workflow.
- Added a `Melodu Workflows` link on the Django Admin home page that opens the Batch Upload workflow.
- Added upload preview with row-level validation, warnings, edit, delete, and commit actions.
- Added update-or-create commit behavior for catalog master data.
- Added product original barcode validation against existing products and duplicate selected rows in the same upload.
- Added stock-in batch upload using the existing `receive_stock()` service so barcode/QR images, stock movements, and audit logs are created by the approved stock-in workflow.
- Added upload commit audit summaries.
- Added tests for parsing, schema validation, staging, row edits, row deletes, update-or-create behavior, barcode uniqueness, stock-in side effects, invalid-row blocking, and Admin/Cashier access.
- Set `LOGIN_URL=/admin/login/` so protected dashboard pages redirect to the real Django Admin login page instead of the unused default accounts login route.

### Melodu Dashboard UX/UI Upgrade

- Added shared `dashboard/base.html` shell with desktop sidebar, mobile bottom navigation, top action area, message stack, language switcher, and scanner modal.
- Added static dashboard CSS and JavaScript under `core/static/core/`.
- Vendored `html5-qrcode` locally for camera and image upload code decoding.
- Added `/dashboard/` home page with role-aware Admin and Cashier summaries.
- Added `/dashboard/api/scan/resolve/` as a read-only code resolver for product codes, original barcodes, batch numbers, and Melodu custom codes.
- Converted POS, stock-in, barcode/QR print, inventory, batch upload, sales, reports, live logs, and system health templates to the shared dashboard shell.
- Added scanner controls to POS, stock-in, barcode/QR print, inventory lookup, and batch upload preview code fields.
- Configured Django i18n with English and Khmer language choices and added a Khmer translation catalog.
- Updated Docker build dependencies to include gettext and compile translation messages.
- Added tests for dashboard home, role-aware navigation, language settings, scan resolver behavior, scanner placement, and dashboard URL resolution.

### Dashboard Product Management

- Added admin-only product management at `/dashboard/products/`.
- Added product search, category, brand, and active status filters.
- Added dashboard product create and edit forms with barcode scan input support.
- Added product create/update audit log creation.
- Added navigation and dashboard quick-action links for product management.
- Added tests for product rendering, filtering, create, edit, audit creation, scan controls, and cashier access blocking.

### Verification

- `docker compose exec -T web python manage.py check`
- `docker compose exec -T web python manage.py test accounts system_logs reports inventory pos audit catalog core`
- `docker compose run --rm -v "$PWD/app:/app" web python manage.py test batch_upload`
- `docker compose run --rm -v "$PWD/app:/app" web python manage.py test`
- `docker compose run --rm -v "$PWD/app:/app" web python manage.py test core`
- `docker compose build web`
- `docker compose run --rm web python manage.py collectstatic --noinput`
- `docker compose run --rm web python manage.py migrate --check`
- `docker compose run --rm web python manage.py test`
- `curl -fsS http://localhost:8000/health/`
- Browser verification screenshots for dashboard, POS, inventory, batch upload, scanner modal, and mobile dashboard were saved under `/tmp/melodu-*.png`.
- `docker compose --env-file .env.example -f docker-compose.prod.yml config`
- `scripts/backup_db.sh`
- `scripts/backup_media.sh`

## 2026-06-09

### V2 Baseline And Stabilization

- Added V2 baseline audit, roadmap, business rules, testing checklist, deployment runbook, and feature backlog documentation.
- Chose active sellable stock as the default report inclusion rule for stock and low-stock reports.
- Added the `expire_batches` maintenance command for audited expired-stock processing without adding a scheduler dependency.
- Hardened backup/restore scripts with explicit compose targeting and restore confirmation.
- Set report exports as the first low-risk V2 feature family after stabilization.

### V2 Phase 2A UX Stabilization

- Added inline quick-create for Category and Brand on Product create/edit.
- Added inline quick-create for Supplier on Stock-In.
- Added an Admin-only catalog quick-create JSON endpoint with CSRF protection, duplicate-name validation, and audit logging.
- Added a shared dashboard quick-create modal that appends and selects the new option without losing unsaved form data.

### V2 Phase 2B Dashboard Access And POS UX Stabilization

- Added dashboard-specific `/dashboard/login/` and POST-only `/dashboard/logout/` routes.
- Switched dashboard auth redirects away from Django Admin login while keeping `/admin/login/` available for Django Admin.
- Standardized dashboard access checks so anonymous users redirect to login and wrong-role users see a friendly 403 page.
- Added friendly 403, 404, and 500 pages without internal error details.
- Hid the Django Admin link from non-admin dashboard users.
- Hardened invalid daily sales report dates and invalid batch-upload template targets.
- Improved POS empty states, unavailable-stock text, checkout button copy, success messaging, and double-submit protection.

### V3 Phase 1 Cost Guardrails, Promotions, And Responsive POS

- Added supplier/product reference costs for vendor-specific expected cost tracking.
- Replaced stock batch `cost_price` with `actual_unit_cost` and optional `landed_unit_cost`.
- Added SaleItem snapshots for cost basis, cost components, original/final price, discounts, promotions, and admin override details.
- Added below-cost sale protection so cashier users are blocked and Admin users must provide an override reason.
- Added simple Admin-managed product/category promotions with percentage, fixed amount, and fixed final price discounts.
- Added best valid promotion selection with no stacking and an explicit `allow_below_cost` flag.
- Added audit logs for cost changes, stock batch cost changes, below-cost sales, promotion below-cost sales, promotion changes, and admin overrides.
- Improved POS responsiveness with promotion labels, touch-friendly quantity steppers, a sticky desktop cart, clearer empty states, and double-submit protection.
- Confirmed local and production compose service lists still include only `postgres` and `web`.

### Catalog Fixes: Product Images And Multi-Animal Products

- Added protected dashboard media serving for `/media/...` so uploaded product images and generated media remain visible when production Nginx only proxies to Django.
- Added an explicit current-image preview to product edit forms; the browser file input still clears after refresh by design, but the saved image now remains visible.
- Added reusable `AnimalTypeOption` records and a Product multi-select relation so one product can target multiple animal types.
- Kept the legacy `Product.animal_type` field populated with the first selected option for backward compatibility.
- Updated product list filters, Django Admin, label printing, batch upload, tests, and docs for multi-animal products.
- Made animal types dashboard-creatable through `/dashboard/animal-types/` and the Product form quick-add modal, with generated upload codes and custom-code batch upload validation.

### Media Storage: MinIO

- Added optional MinIO/S3-compatible media storage controlled by `USE_S3_MEDIA`.
- Added `django-storages[s3]`, S3 storage settings, MinIO compose services, bucket initialization, and `data/minio` persistence.
- Updated protected media handling to redirect authenticated `/media/...` requests to signed object URLs when S3 media is enabled.
- Added MinIO backup/restore scripts and deployment documentation for host Nginx HTTPS proxying.

### Documentation: Current Status

- Added `docs/CURRENT_STATUS.md` as the project handoff source of truth for current architecture, feature state, deployment mode, media storage, backup, verification, known notes, and suggested next work.
- Linked the current status document from `README.md` and tracked it in `docs/TASKS.md`.

## 2026-06-16

### V7-008 Audit, Log, and System Page Polish

- Added read-only summary metrics to the dashboard audit log page.
- Added human-readable disk values and scan-friendly status cards to System Health.
- Added explicit live-log safety copy for sanitized logs and 5-second auto-refresh.
- Split Live Logs into guidance, Errors, and Application panels while preserving existing redaction behavior.
- Verified with mounted-source `manage.py check`, 15 focused audit/system tests, and 119 V7 regression tests.

### V7-009 Empty, Error, and Access-State Polish

- Added `What to do next` guidance to dashboard 403, 404, and 500 pages.
- Removed the misleading always-on `EVENT LOGGED` footer from non-permission error pages while keeping `AUDIT TRAIL ACTIVE` for access denied states.
- Improved empty states for Batch Upload recent jobs, Sales History, User Management, and Label Templates.
- Verified with mounted-source `manage.py check`, 16 focused empty/error/access-state tests, and 139 V7 regression tests.

### V7-010 Mobile and Tablet Usability Pass

- Added responsive guards for topbar action wrapping, non-POS table scrollers, scanner modal sizing, payment dialog sizing, auth/error page scrolling, and mobile nav label truncation.
- Preserved the compact POS cart table on desktop and phone after browser metrics caught an early over-broad table min-width rule.
- Refreshed collected static after CSS changes and restarted the temporary browser-test server so the current hashed stylesheet was verified.
- Browser-checked phone, tablet, desktop, and phone scanner modal layouts for document-level overflow and expected nav/sidebar behavior.
- Verified with mounted-source `manage.py check`, 36 focused responsive tests, and 140 V7 regression tests.

### V7-011 English and Khmer Wording Consistency Review

- Wrapped V7 Python-origin form/help/error strings with Django gettext so the language switch covers more than template text.
- Added focused Khmer translations for V7 product, inventory, POS, batch upload, audit, live logs, system health, labels, promotions, and error-state wording.
- Compiled the Khmer gettext catalog (`django.mo`) so translations are available at runtime.
- Browser-checked Khmer Product, Stock Overview, and friendly 404 pages after switching languages through the dashboard selector.
- Verified with `msgfmt --check`, mounted-source `manage.py check`, 29 focused translation/form/error tests, and 142 V7 regression tests.

### V7-012 QA And Release Preparation

- Finalized `docs/versions/v7/V7_QA_CHECKLIST.md` with completed scope, functional, permission, UI/UX, data-safety, audit/logging, documentation, regression, release, and rollback checks.
- Finalized `docs/versions/v7/V7_RELEASE_NOTE.md` with actual V7 changes, non-changes, testing notes, browser checks, rollback notes, and V8 recommendation.
- Marked V7 scope, task list, and master completion tracker as complete.
- Closed V7 with all tasks V7-001 through V7-012 complete and no database migrations required.

### V8-011 QA And Release Preparation

- Finalized `docs/versions/v8/V8_QA_CHECKLIST.md` with completed scope, functional, permission, UI/UX, data-safety, audit/logging, documentation, regression, release, and rollback checks.
- Finalized `docs/versions/v8/V8_RELEASE_NOTE.md` with actual inventory, label, barcode/QR, promotion, POS warning, and traceability changes.
- Marked V8 scope, task list, and master completion tracker as complete.
- Closed V8 with all tasks V8-001 through V8-011 complete and no database migrations required.
- Verified with mounted-source `manage.py check`, `collectstatic --noinput`, the full 311-test Django suite, desktop browser smoke checks, phone-width browser smoke checks, and a clean browser console.

### V9-001 Owner Dashboard And Reporting Audit

- Created `docs/versions/v9/V9_OWNER_CONTROL_AUDIT.md` to map current owner dashboard, report launcher, sales, staff, stock, promotion, exception, audit, system, backup, and closing-control coverage.
- Marked V9 as in progress and V9-001 complete in the version tracker.
- Confirmed V9 implementation should stay read-only for reports/audit/system pages unless a documented bug requires service changes.

### V9-002 Daily Sales Report Improvement

- Added explicit daily sales report definitions so completed sales count as revenue and cancelled sales are treated as exceptions.
- Added completed/cancelled counts, gross sales, discounts, completed revenue, average sale, payment breakdown, and sale-detail links.
- Added cost of goods and gross margin metrics behind the existing cost-visibility rule.
- Verified with mounted-source `reports.tests.ReportPageTests` (12 tests OK).

### V9-003 Staff Sales And Cashier Accountability Report

- Extended Staff Sales with cashier accountability signals: cancellations, receipt reprints, below-cost overrides, discounts, average sale, and optional cost/margin.
- Reused `AuditLog.Action.RECEIPT_PRINT` for reprint counts instead of adding a sale counter field.
- Kept the report read-only and permission-gated.
- Verified with mounted-source `reports.tests.ReportPageTests` (13 tests OK).

### V9-004 Stock, Low-stock, And Expiry Reporting Review

- Added report definition panels to Stock Summary, Low Stock, and Expiry reports.
- Added out-of-stock, healthy, and review-now risk counts where relevant.
- Sorted low-stock rows by reorder gap so the most urgent products appear first.
- Kept stock calculations based on active, unexpired sellable batches only.
- Verified with mounted-source `reports.tests.ReportPageTests` (13 tests OK).

### V9-005 Promotion And Below-cost Reporting

- Added a new Promotion & Below-cost Report under Reports.
- Aggregated promotion usage, discounts, final sales, below-cost lines, overrides, and optional cost/margin from completed sale-item snapshots.
- Added a below-cost review table that links risky promoted lines back to sale detail.
- Verified with mounted-source `reports.tests.ReportPageTests` (15 tests OK).

### V9-006 Sale Cancellation And Receipt Reprint Tracking

- Added a sale status filter and exception summary cards to Sales History.
- Added receipt reprint count and an audit-backed Exception Tracking table to Sale Detail.
- Kept cancellation, stock reversal, receipt rendering, and audit creation behavior unchanged.
- Verified with mounted-source `pos.tests.SalesCancellationTests` and `pos.tests.ReceiptTests` (10 tests OK).

### V9-007 Audit Log Readability And Filters

- Added broad audit search and object-type filtering.
- Added audit summary cards for entries, risk events, modules, users, read-only mode, and ordering.
- Marked risk actions with review badges and displayed object type/id metadata in the audit table.
- Kept the audit dashboard read-only.
- Verified with mounted-source `audit.tests.AuditLogDashboardTests` (5 tests OK).

### V9-008 System Logs And Health Review

- Added overall health status, disk used percentage/status, and operator notes to System Health.
- Added displayed app/error log line counts to Live Logs.
- Preserved existing log redaction and access restrictions.
- Verified with mounted-source `system_logs.tests.SystemLogTests` (6 tests OK).

### V9-009 Daily Closing Control Checklist

- Added a read-only Daily Closing Checklist under Reports.
- Linked closing review to Daily Sales, Staff Sales, Promotion & Below-cost, Low Stock, Expiry, and System Health evidence.
- Added shared checklist styling in the dashboard CSS.
- Kept the checklist operational only; no accounting, payroll, final close, or closing record model was added.
- Verified with mounted-source `reports.tests.ReportPageTests` (16 tests OK).

### V9-010 Backup And Reset Visibility Review

- Added Backup / Reset Safeguards to System Health with backup command names and runbook paths.
- Reconfirmed there is intentionally no dashboard reset button.
- Kept backup, restore, and reset script behavior unchanged.
- Verified with mounted-source `system_logs.tests.SystemLogTests` (6 tests OK).

### V9-011 QA And Release Preparation

- Finalized `docs/versions/v9/V9_QA_CHECKLIST.md` with completed scope, functional, permission, UI/UX, data-safety, audit/logging, documentation, regression, release, and rollback checks.
- Finalized `docs/versions/v9/V9_RELEASE_NOTE.md` with actual owner-control report, audit, system, closing, and backup/reset visibility changes.
- Marked V9 scope, task list, PRD/TRD, and master completion tracker as complete.
- Closed V9 with all tasks V9-001 through V9-011 complete and no database migrations required.
- Verified with mounted-source `manage.py check`, `collectstatic --noinput`, the full 319-test Django suite, desktop browser smoke checks, phone-width browser smoke checks, and a clean browser console.

### V10-001 Through V10-010 Scale-readiness Planning

- Completed V10 as a planning/governance package, not an application implementation.
- Added V10 evidence docs for multi-store readiness, store/location model planning, store-level permissions, store-level inventory, store-level reporting, store settings separation, deployment/backup hardening, monitoring/logging, data/audit retention, and performance/database review.
- Created `docs/decisions/ADR-0008-multi-store-readiness-boundary.md` to make clear that V10 does not add store schema, migrations, store selectors, permission behavior, routes, templates, or service changes.
- Confirmed future multi-store implementation requires a separate approved task covering model, permission, migration, report, UI, and rollback plans.

### V10-011 QA And Release Preparation

- Finalized `docs/versions/v10/V10_QA_CHECKLIST.md` and `docs/versions/v10/V10_RELEASE_NOTE.md`.
- Marked V10 scope, PRD, TRD, task list, and master completion tracker as complete.
- Updated README, current status, version roadmap, implementation backlog, docs index, ADR index, and `docs/TASKS.md` so V7-V10 completion is visible from the handoff path.
- Verified V10 as documentation-only with file-structure checks and `git diff --check`.
