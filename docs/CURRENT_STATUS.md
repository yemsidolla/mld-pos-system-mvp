# Current Project Status

Last updated: 2026-06-16

Melodu POS is currently a Django monolith for Melodu Pet Store. The project has
grown beyond the original V1 MVP checklist and now includes the V1 core,
dashboard UX, batch upload, scanner workflows, role/capability management,
receipt/label improvements, product classification, and optional Garage media
storage.

V7, V8, and V9 are complete with implementation evidence in
`docs/versions/VERSION_COMPLETION_TRACKER.md`. V10 is complete as a
multi-store/scale-readiness planning package only; it does not add multi-store
schema, permissions, routes, templates, or services.

## Documentation Authority

Before planning or implementing future work, use this read order:

1. `docs/STANDARD_WAY_OF_WORKING.md`
2. `README.md`
3. `docs/CURRENT_STATUS.md`
4. `docs/DESIGN_SYSTEM.md` when UI is affected
5. `docs/product/11_DOCUMENTATION_MAP.md`
6. `docs/README.md` for the full docs folder index
7. `docs/product/00_CURRENT_SYSTEM_MAP.md`
8. Relevant version docs and guides
9. `docs/product/09_IMPLEMENTATION_BACKLOG.md` or `docs/TASKS.md`
10. `docs/DEVELOPMENT_LOG.md`

The controlled foundation reset added:

- Product docs under `docs/product/`
- V6 reset docs under `docs/versions/v6/`
- ADRs under `docs/decisions/`
- Durable V7-V10 completion tracking under `docs/versions/VERSION_COMPLETION_TRACKER.md`

Older docs are organized under `docs/legacy/`. When documents overlap,
start from `docs/product/11_DOCUMENTATION_MAP.md`.

## Current Architecture

- Backend: Django 5.2 monolith.
- Database: PostgreSQL 16.
- Runtime: Docker Compose with Gunicorn/Django.
- Public reverse proxy: host Nginx on the VPS, outside Docker.
- Static files: WhiteNoise from collected static files.
- Media files:
  - Local filesystem mode: `USE_S3_MEDIA=False`, files under `data/media`.
  - Garage mode: `USE_S3_MEDIA=True`, files under `data/garage` through
    S3-compatible Django storage.
- Object storage: optional Garage service in Docker Compose.
- Auth: local Django login by default, with Authentik/OIDC support available.
- Frontend: Django templates, shared dashboard shell, static CSS, vanilla JS.
- Scanner: local `html5-qrcode` vendor asset plus server-side image decoding.

## Daily Interfaces

- Dashboard: `/dashboard/`
- POS: `/dashboard/pos/`
- Receipt: `/dashboard/pos/receipt/<sale_id>/`
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

Authoritative route and capability map: `docs/product/00_CURRENT_SYSTEM_MAP.md`.

## Test Coverage

319 automated test methods across 10 custom Django apps in the latest full-suite
workspace verification. Run:

```bash
docker compose run --rm web python manage.py test
```

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

### Garage

Use this for production or larger image workflows:

```env
USE_S3_MEDIA=True
GARAGE_RPC_SECRET=replace-with-64-hex-from-openssl-rand-hex-32
S3_STORAGE_BUCKET_NAME=melodu-media
S3_ACCESS_KEY_ID=melodu_garage
S3_SECRET_ACCESS_KEY=replace-with-strong-password
S3_ENDPOINT_URL=https://melodu-media.khlovepet.com
S3_REGION_NAME=us-east-1
S3_QUERYSTRING_AUTH=True
S3_QUERYSTRING_EXPIRE=3600
```

Docker Compose includes:

- `garage`
- `postgres`
- `web`

After first start, run `scripts/bootstrap_garage.sh` once to assign layout,
create the bucket, and import the S3 key.

Production Garage S3 should be exposed through host Nginx over HTTPS. Do not
expose raw Garage ports publicly. Admin and RPC stay on loopback.

See `docs/guides/GARAGE_STORAGE_GUIDE.md`.

## Permissions State

The system now has role/capability behavior beyond the original Admin/Cashier
split.

Key protections:

- Cashier users are restricted to POS-focused workflows.
- Management, reports, logs, audit, users, settings, roles, costs, promotions,
  stock-in, and inventory are capability-gated.
- Cashier users are blocked from Django Admin even if accidentally marked staff.
- Owner/Manager/Admin-style capabilities are documented in
  `docs/reference/PERMISSION_MATRIX.md` and V6 permission docs.

## Auth State

Default mode:

```env
AUTH_MODE=local
```

OIDC/Authentik mode is available through the V6 docs:

- `docs/versions/v6/V6_AUTHENTIK_AUTH_ARCHITECTURE.md`
- `docs/versions/v6/V6_AUTHENTIK_SETUP_GUIDE.md`
- `docs/versions/v6/V6_CURRENT_AUTH_AUDIT.md`

Keep local login enabled as an emergency path unless the deployment is fully
verified.

## Deployment State

Production should use build → migrate → start (migrate before serve):

```bash
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml run --rm web python manage.py migrate
docker compose -f docker-compose.prod.yml up -d
docker compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
docker compose -f docker-compose.prod.yml restart web
```

Additive migrations are safe with old containers still serving; new code against
an unmigrated database is not. Do not reorder to `up -d --build` then migrate.

Host Nginx proxies:

- Main app domain to `127.0.0.1:${WEB_HOST_PORT:-8001}`.
- Optional media domain to `127.0.0.1:${GARAGE_S3_HOST_PORT:-3900}`.

Important production docs:

- `docs/guides/DEPLOYMENT_GUIDE.md`
- `docs/operations/DEPLOYMENT_RUNBOOK.md`
- `docs/operations/PRODUCTION_CHECKLIST.md`
- `docs/guides/GARAGE_STORAGE_GUIDE.md`
- `docs/guides/BACKUP_GUIDE.md`

## Backup State

Database backup:

```bash
scripts/backup_db.sh
```

Filesystem media backup when `USE_S3_MEDIA=False`:

```bash
scripts/backup_media.sh
```

Garage media backup when `USE_S3_MEDIA=True`:

```bash
scripts/backup_garage.sh
```

Restore scripts:

```bash
scripts/restore_db.sh
scripts/restore_media.sh
scripts/restore_garage.sh
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

Latest recorded result:

```text
319 tests OK
```

## Known Operational Notes

- Production has always used local filesystem media (`USE_S3_MEDIA` unset /
  False; no MinIO). Existing files under `data/media` are not automatically
  migrated to Garage. After enabling Garage, new uploads go to Garage; migrate
  existing local media deliberately with a backup in place via
  `scripts/migrate_media_to_garage.sh` (`data/media` → Garage).
- When `USE_S3_MEDIA=True`, browser-visible media URLs must use an HTTPS
  endpoint reachable by phones and desktops.
- Production Authentik/OIDC group claims, phone scanner behavior, physical
  printer output, and backup/restore recovery should be verified against the
  live VPS or a production-like clone before being treated as fully proven.

## Suggested Next Work

- Decide final production media domain, for example
  `melodu-media.khlovepet.com`.
- Add host Nginx config for the media domain before enabling Garage in
  production.
- Migrate existing `data/media` files to Garage with
  `scripts/migrate_media_to_garage.sh` only after confirming backup and restore.
- Use `docs/product/09_IMPLEMENTATION_BACKLOG.md` and `docs/TASKS.md` for the
  next approved implementation scope.
- Use `docs/versions/VERSION_COMPLETION_TRACKER.md` before starting any future
  version work, so completed V7-V10 tasks are not duplicated or removed.
- Treat future multi-store implementation as unbuilt until a new approved task
  defines exact model, permission, migration, report, and UI changes.
