# Melodu POS & Inventory Control System

Version 1 MVP is a Django monolith for Melodu Pet Store.

## Technology

- Django monolith
- Django Admin for internal model management
- Custom Django pages for POS, stock-in, barcode/QR printing, reports, live logs, and system health
- PostgreSQL database
- Docker Compose hosting
- Gunicorn for Django
- External host Nginx reverse proxy
- Docker-backed static, media, log, and database persistence
- Optional MinIO/S3-compatible media storage for uploaded and generated media

## Core Business Rule

All stock is controlled at stock batch level.

- Product is master data.
- StockBatch is real sellable stock.
- SaleItem must always link to StockBatch.
- Stock deduction must always happen from StockBatch.
- Stock quantity must never become negative.
- Every stock change must create InventoryMovement.
- Every important business action must create AuditLog.
- Every backend error must be written to logs.

## Version 1 Boundary

Version 1 does not include Next.js, Node.js, Redis, Celery, customer accounts, loyalty points, promotions, multi-branch support, online payment gateway integration, external APIs, or a mobile app.

## Implemented Phases

### Phase 0: Project Bootstrap

- Django project and required apps are created.
- Docker Compose runs PostgreSQL, Gunicorn/Django, and optional MinIO media storage. It does not include an internal Nginx container.
- Static, local media, MinIO object data, database, and log folders persist under `data/`.
- `/health/` checks the database connection.

### Phase 1: Master Data

- `Category`, `Brand`, `Supplier`, and `Product` are implemented in `catalog`.
- Product code is unique.
- Original barcode is unique when provided, and products without a barcode are allowed.
- Product prices use `DecimalField`.
- Product image upload is available through Django Admin.
- Django Admin supports product search by name, product code, and original barcode.
- Django Admin supports product filtering by active status, category, and brand.
- Product management is available in the Melodu dashboard at `/dashboard/products/` for Admin users.
- The dashboard product page supports search, category, brand, active status filters, create, edit, and barcode scan input.

### Phase 2: Audit Foundation

- `AuditLog` is implemented in `audit`.
- Audit entries capture user, action, module, object metadata, old/new values, IP address, user agent, and timestamp.
- `create_audit_log()` is the shared helper for future business workflows.
- Login success and login failure are audited with Django auth signals.
- Audit logs are visible in Django Admin but cannot be added or deleted through normal admin actions.
- Login failure auditing does not persist submitted passwords.

### Phase 3: Stock-In and Batch

- `StockBatch` and `InventoryMovement` are implemented in `inventory`.
- Batch numbers use the approved `BYYNNNN` format.
- Custom codes use `[ORIGINAL_BARCODE]-M-[EXPIRY_YYMMDD]-[BATCH_NO]`.
- Stock-in requires active product, active supplier, positive quantity, expiry date, and product original barcode.
- Stock-in creates barcode and QR PNG images under media storage.
- Stock-in creates one `InventoryMovement` with movement type `STOCK_IN`.
- Stock-in creates one audit log with action `STOCK_IN`.
- The custom stock-in page is available at `/dashboard/stock-in/` for staff users.

### Phase 4: Barcode / QR Print

- The label print page is available at `/dashboard/barcode-print/` for staff users.
- Labels are generated from active stock batches.
- Label preview supports a configurable label quantity.
- Each label includes store name, product name, price, expiry date, batch number, barcode, QR code, and custom code.
- Recording a print action creates an audit log with action `BARCODE_PRINT`.

### Phase 5: POS Sale

- `Sale` and `SaleItem` are implemented in `pos`.
- `SaleItem.stock_batch` is required.
- The POS page is available at `/dashboard/pos/` for staff users.
- Original barcode scans return product information plus sellable stock batches; cashier must select a batch.
- Melodu custom code scans identify the exact stock batch.
- Sale confirmation runs in a database transaction.
- Stock deduction always happens from `StockBatch.quantity_available`.
- Sold-out batches are marked `SOLD_OUT`.
- Expired, inactive, unavailable, or insufficient stock cannot be sold.
- Sale confirmation creates sale items, sale inventory movements, and a `SALE_CREATE` audit log.
- Receipts are available at `/dashboard/pos/receipt/<sale_id>/`.
- Sale numbers use `SYYMMDDNNNN`.

### Phase 6: Sales History and Cancellation

- Sales history is available at `/dashboard/sales/` for superusers.
- Sales can be filtered by date range, cashier, and payment method.
- Sale detail is available at `/dashboard/sales/<sale_id>/`.
- Completed sales can be cancelled only by superusers.
- Cancellation requires a reason.
- Cancellation restores quantity to each original stock batch.
- Cancellation creates `RETURN` inventory movements.
- Cancellation creates a `SALE_CANCEL` audit log.

### Phase 7: Inventory Adjustment and Expiry Control

- Inventory summary is available at `/dashboard/inventory/` for superusers.
- Batch detail is available at `/dashboard/inventory/batches/<batch_id>/`.
- Product stock summary shows total available quantity by product.
- Batch detail shows expiry status: Expired, Critical, Warning, or Normal.
- Inventory adjustment requires a reason and cannot make stock negative.
- Damaged stock handling reduces available stock, creates `DAMAGE` movement, and audits the action.
- Expired stock handling removes available stock, marks the batch `EXPIRED`, creates `EXPIRED` movement, and audits the action.

### Phase 8: Reports

- Reports index is available at `/dashboard/reports/` for superusers.
- Daily sales report is available at `/dashboard/reports/daily-sales/`.
- Stock summary report is available at `/dashboard/reports/stock-summary/`.
- Low stock report is available at `/dashboard/reports/low-stock/`.
- Expiry report is available at `/dashboard/reports/expiry/`.
- Stock movement report is available at `/dashboard/reports/stock-movements/`.
- Staff sales report is available at `/dashboard/reports/staff-sales/`.
- Reports are simple HTML tables in Version 1.

### Phase 9: Live Backend Logs and System Health

- Live backend logs are available at `/dashboard/live-logs/` for superusers.
- The live log page refreshes every 5 seconds.
- Logs are read from `logs/app.log` and `logs/error.log`.
- Secret-like values are redacted from displayed log lines.
- System health is available at `/dashboard/system-health/` for superusers.
- System health shows database status, app version, disk usage, log writable status, last sale time, last stock-in time, and last error line.
- Cashiers cannot access live logs or system health.

### Phase 10: Permission and Security

- Default Django groups `Admin` and `Cashier` are created after migrations.
- Superusers and `Admin` group members can access management pages.
- `Cashier` group members can access POS and receipts only.
- Cashier users are blocked from Django Admin even if accidentally marked staff.
- Stock-in, barcode print, inventory, sales history/cancellation, reports, audit admin, live logs, system health, and user management are restricted away from cashier users.
- CSRF middleware remains enabled.
- Production cookie/security settings are environment-configurable.

### Phase 11: Production Deployment and Backup

- Production Compose settings are available in `docker-compose.prod.yml` for PostgreSQL, Django, and optional MinIO media storage.
- Production HTTPS/reverse proxy is handled by Nginx on the host, outside Docker.
- Production setup steps are documented in `docs/guides/DEPLOYMENT_GUIDE.md`.
- Backup and restore steps are documented in `docs/guides/BACKUP_GUIDE.md`.
- Production checklist is documented in `docs/operations/PRODUCTION_CHECKLIST.md`.
- Database backup script is `scripts/backup_db.sh`.
- Media backup script is `scripts/backup_media.sh`.
- Garage media backup script is `scripts/backup_garage.sh` when `USE_S3_MEDIA=True`.
  It requires Garage to be stopped (or `GARAGE_BACKUP_STOP=yes`) for a consistent
  archive; a hot tar of a running Garage can capture inconsistent metadata.
- Migrating existing filesystem media into Garage uses
  `scripts/migrate_media_to_garage.sh`.
- Database restore script is `scripts/restore_db.sh`.
- Generated backups are ignored by git via `backups/`.

### Batch Upload Feature

- Batch upload is available at `/dashboard/batch-upload/` for Admin users only.
- Django Admin links to the batch upload workflow under the `Melodu Workflows` section.
- Supported upload targets are categories, brands, suppliers, products, and stock-in.
- POS sales, audit logs, reports, and system logs are not importable because they must be generated by controlled application workflows.
- CSV and XLSX files are supported.
- Uploads create database-backed preview jobs and row records so validation results survive page refresh.
- Preview rows can be edited or deleted before commit.
- Invalid rows are never committed.
- Category, brand, and supplier uploads use `name` as the update-or-create identifier.
- Product uploads use `product_code` as the update-or-create identifier.
- Product upload validates category and brand names when provided.
- Product original barcode uniqueness is validated against existing products and other selected rows in the same upload.
- Stock-in upload requires existing active products, active suppliers, positive quantity, expiry date, cost price, selling price, and product original barcode.
- Stock-in upload always creates new stock batches and uses the existing `receive_stock()` service.
- Committed stock-in rows create `StockBatch`, barcode image, QR image, `InventoryMovement`, and `AuditLog` records.
- Each committed upload job creates an audit summary with created, updated, skipped, failed, and total row counts.

### Melodu Dashboard UX/UI Upgrade

- `/dashboard/` is the main daily-work interface for Admin and Cashier users.
- Django Admin remains available at `/admin/` for raw model inspection, users, groups, and emergency maintenance.
- The custom dashboard uses a shared shell with desktop sidebar, mobile bottom navigation, top action area, messages, reusable cards, tables, forms, alerts, badges, and modals.
- Dashboard navigation is role-aware: Cashier users see POS-focused navigation, while Admin users see inventory, stock-in, batch upload, labels, sales, reports, and system links.
- Existing business services remain the source of truth for stock-in, sale confirmation, cancellation, batch upload commit, inventory movements, and audit logs.
- A reusable scanner modal supports camera scan, image upload decode, and manual code entry.
- Scanner controls are available on POS, stock-in, barcode/QR print, inventory lookup, and batch upload preview code fields.
- `/dashboard/api/scan/resolve/` is a read-only resolver endpoint for product, barcode, batch number, and Melodu custom code metadata.
- The scanner does not save images or mutate sales, stock, uploads, movements, or audits.
- English and Khmer are configured through Django i18n and a dashboard language switcher.
- Production camera scanning requires HTTPS; localhost is allowed for development.
