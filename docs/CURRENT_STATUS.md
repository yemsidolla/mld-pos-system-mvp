# Current Project Status

Last updated: 2026-06-16

Melodu POS is currently a Django monolith for Melodu Pet Store. The project has
grown beyond the original V1 MVP checklist and now includes the V1 core,
dashboard UX, batch upload, scanner workflows, role/capability management,
receipt/label improvements, product classification, and optional MinIO media
storage.

## Current Architecture

- Backend: Django 5.2 monolith.
- Database: PostgreSQL 16.
- Runtime: Docker Compose with Gunicorn/Django.
- Public reverse proxy: host Nginx on the VPS, outside Docker.
- Static files: WhiteNoise from collected static files.
- Media files:
  - Local filesystem mode: `USE_S3_MEDIA=False`, files under `data/media`.
  - MinIO mode: `USE_S3_MEDIA=True`, files under `data/minio` through
    S3-compatible Django storage.
- Object storage: optional MinIO service in Docker Compose.
- Auth: local Django login by default, with Authentik/OIDC support available.
- Frontend: Django templates, shared dashboard shell, static CSS, vanilla JS.
- Scanner: local `html5-qrcode` vendor asset plus server-side image decoding.

## Daily Interfaces

- Dashboard: `/dashboard/`
- POS: `/dashboard/pos/`
- Products: `/dashboard/products/`
- Animal Types: `/dashboard/animal-types/`
- Categories: `/dashboard/categories/`
- Brands: `/dashboard/brands/`
- Suppliers: `/dashboard/suppliers/`
- Stock-In: `/dashboard/stock-in/`
- Inventory: `/dashboard/inventory/`
- Batch Upload: `/dashboard/batch-upload/`
- Label Print: `/dashboard/labels/print/`
- Promotion Labels: `/dashboard/labels/promotions/`
- Sales History: `/dashboard/sales/`
- Reports: `/dashboard/reports/`
- Live Logs: `/dashboard/live-logs/`
- System Health: `/dashboard/system-health/`
- Django Admin: `/admin/`

Django Admin remains available for raw/back-office inspection and emergency
maintenance, but daily work should happen in the Melodu Dashboard.

## Implemented Business Core

- Product master data.
- Batch-level inventory control.
- Stock-in creates `StockBatch`, barcode image, QR image, `InventoryMovement`,
  and `AuditLog`.
- POS sales always deduct from selected stock batches.
- Sale cancellation restores stock to original batches.
- Inventory adjustment prevents negative stock.
- Expiry and damaged-stock handling create inventory movements and audits.
- Reports cover sales, stock, low stock, expiry, stock movements, and staff
  sales.
- Critical workflows are transaction-protected.
- Money values use `Decimal`.

## Catalog State

Products now support:

- Product image upload.
- Category and Brand.
- Supplier reference costs.
- Multiple animal types through `AnimalTypeOption`.
- Life stage.
- Flexible product tags.
- Active/inactive status.
- Product list photo column.
- Dashboard design-system product form.

Animal types are now dashboard-creatable:

- Full management page: `/dashboard/animal-types/`
- Inline quick-add from product create/edit.
- Code can be auto-generated from name, for example `Reptile` to `REPTILE`.
- Product upload validates active animal type codes.

## Batch Upload State

Batch upload supports CSV and XLSX with preview/edit/delete/commit workflow for:

- Categories.
- Brands.
- Suppliers.
- Products.
- Stock-in.

Controlled records are intentionally not importable:

- POS sales.
- Audit logs.
- Reports.
- System logs.

Product upload now includes optional classification fields:

- `animal_type`
- `life_stage`
- `tags`

Stock-in upload still uses the existing `receive_stock()` service so movements,
barcode/QR files, and audit logs are created consistently.

## Scanner State

The dashboard scanner supports:

- Device camera scan.
- Uploaded image decode.
- Manual fallback input.
- Read-only scan resolver API.

Scanner buttons are available in:

- POS.
- Stock-in product lookup.
- Barcode/QR print.
- Inventory lookup.
- Batch upload preview fields.
- Product barcode fields.

Production camera scanning requires HTTPS. Localhost works for development.

## Media Storage State

The project now supports two media modes.

### Local Filesystem

Use this for simple development:

```env
USE_S3_MEDIA=False
```

Media goes to `data/media`.

### MinIO

Use this for production or larger image workflows:

```env
USE_S3_MEDIA=True
MINIO_ROOT_USER=melodu_minio
MINIO_ROOT_PASSWORD=replace-with-strong-password
S3_STORAGE_BUCKET_NAME=melodu-media
S3_ACCESS_KEY_ID=melodu_minio
S3_SECRET_ACCESS_KEY=replace-with-strong-password
S3_ENDPOINT_URL=https://melodu-media.khlovepet.com
S3_REGION_NAME=us-east-1
S3_QUERYSTRING_AUTH=True
S3_QUERYSTRING_EXPIRE=3600
```

Docker Compose includes:

- `minio`
- `minio-init`
- `postgres`
- `web`

Production MinIO should be exposed through host Nginx over HTTPS. Do not expose
raw MinIO ports publicly.

See `docs/MINIO_STORAGE_GUIDE.md`.

## Permissions State

The system now has role/capability behavior beyond the original Admin/Cashier
split.

Key protections:

- Cashier users are restricted to POS-focused workflows.
- Management, reports, logs, audit, users, settings, roles, costs, promotions,
  stock-in, and inventory are capability-gated.
- Cashier users are blocked from Django Admin even if accidentally marked staff.
- Owner/Manager/Admin-style capabilities are documented in
  `docs/PERMISSION_MATRIX.md` and V6 permission docs.

## Auth State

Default mode:

```env
AUTH_MODE=local
```

OIDC/Authentik mode is available through the V6 docs:

- `docs/V6_AUTHENTIK_AUTH_ARCHITECTURE.md`
- `docs/V6_AUTHENTIK_SETUP_GUIDE.md`
- `docs/V6_CURRENT_AUTH_AUDIT.md`

Keep local login enabled as an emergency path unless the deployment is fully
verified.

## Deployment State

Production should use:

```bash
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml exec web python manage.py migrate
docker compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
docker compose -f docker-compose.prod.yml restart web
```

Host Nginx proxies:

- Main app domain to `127.0.0.1:${WEB_HOST_PORT:-8001}`.
- Optional media domain to `127.0.0.1:${MINIO_API_HOST_PORT:-9000}`.

Important production docs:

- `docs/DEPLOYMENT_GUIDE.md`
- `docs/DEPLOYMENT_RUNBOOK.md`
- `docs/PRODUCTION_CHECKLIST.md`
- `docs/MINIO_STORAGE_GUIDE.md`
- `docs/BACKUP_GUIDE.md`

## Backup State

Database backup:

```bash
scripts/backup_db.sh
```

Filesystem media backup when `USE_S3_MEDIA=False`:

```bash
scripts/backup_media.sh
```

MinIO media backup when `USE_S3_MEDIA=True`:

```bash
scripts/backup_minio.sh
```

Restore scripts:

```bash
scripts/restore_db.sh
scripts/restore_media.sh
scripts/restore_minio.sh
```

Back up PostgreSQL and the active media storage together because product,
store, label, barcode, QR, and KHQR records reference stored media paths.

## Current Verification

Latest completed verification in this workspace:

```bash
docker compose --env-file .env.example config --services
docker compose --env-file .env.example -f docker-compose.yml -f docker-compose.local.yml config --services
docker compose --env-file .env.example -f docker-compose.prod.yml config --services
docker compose build web
docker compose run --rm web python manage.py check
docker compose run --rm -e USE_S3_MEDIA=True web python manage.py check
docker compose run --rm web python manage.py test
```

Result:

```text
289 tests OK
```

## Known Operational Notes

- The local workspace currently has uncommitted implementation changes for:
  - Dashboard-creatable animal types.
  - Product form/list updates.
  - MinIO media storage.
  - MinIO documentation and backup scripts.
- `.claude/` is an unrelated untracked local folder and should not be included
  unless explicitly needed.
- Existing production files under `data/media` are not automatically migrated to
  MinIO. After enabling MinIO, new uploads go to MinIO; old media should be
  migrated deliberately with a backup in place.
- When `USE_S3_MEDIA=True`, browser-visible media URLs must use an HTTPS
  endpoint reachable by phones and desktops.

## Suggested Next Work

- Commit and push the current implementation after review.
- Decide final production media domain, for example
  `melodu-media.khlovepet.com`.
- Add host Nginx config for the media domain before enabling MinIO in
  production.
- Migrate any existing `data/media` files to MinIO only after confirming backup
  and restore.
- Continue V2/V3/V4/V5/V6 work from the documented task tracker rather than
  reopening the original Phase 0-11 plan.
