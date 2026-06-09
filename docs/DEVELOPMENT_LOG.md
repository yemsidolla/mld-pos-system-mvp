# Development Log

## 2026-06-09

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
- Documented in `docs/LABEL_TEMPLATE_GUIDE.md`.
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
- Documented in `docs/PRINTER_RECEIPT_GUIDE.md`.
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
- Documented in `docs/PRODUCT_CLASSIFICATION_GUIDE.md` and the batch-upload
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
- Documented the plan and matrix in `docs/V4_PHASE_PLAN.md` and
  `docs/PERMISSION_MATRIX.md`; updated `docs/USER_MANAGEMENT_GUIDE.md`.
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
- Added `docs/BACKUP_GUIDE.md`.
- Added `docs/PRODUCTION_CHECKLIST.md`.
- Expanded `docs/DEPLOYMENT_GUIDE.md` with VPS deployment, role setup, backup, and restore steps.
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
