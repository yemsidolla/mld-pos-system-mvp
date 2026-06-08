# Development Log

## 2026-06-06

### Phase 0: Project Bootstrap

- Created the Django monolith project under `app/`.
- Added Docker Compose services for PostgreSQL, web, and Nginx.
- Added `/health/`, static/media/log/database persistence folders, and starter documentation.
- Verified Docker startup, Django migrations, collectstatic, admin login redirect, health check, and restart persistence.
- Fixed Nginx host forwarding to preserve `localhost:8000` for Django CSRF checks.

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

- Added `docker-compose.prod.yml` with production restart policies and port 80 Nginx binding.
- Updated `.env.example` with app version and production security fields.
- Added backup and restore scripts under `scripts/`.
- Added `docs/BACKUP_GUIDE.md`.
- Added `docs/PRODUCTION_CHECKLIST.md`.
- Expanded `docs/DEPLOYMENT_GUIDE.md` with VPS deployment, role setup, backup, and restore steps.
- Updated README with current MVP status and operational links.
- Verified production Compose config with `.env.example`.
- Ran database and media backup scripts successfully against the local stack.

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
