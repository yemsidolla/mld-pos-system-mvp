# Melodu POS & Inventory Control System

Version 1 MVP for Melodu Pet Store.

This project is a Django monolith using PostgreSQL, Docker Compose, Gunicorn, and WhiteNoise. Version 1 uses Django Admin for raw internal management and a polished Melodu Dashboard for daily POS, stock-in, barcode/QR printing, batch upload, inventory, reports, live backend logs, and system health. Production HTTPS is handled by Nginx on the host, not by an internal Docker Nginx container.

## Phase Status

Current implementation: Version 1 MVP phases 0 through 11 plus the batch upload feature and Melodu Dashboard UX/UI upgrade.

The MVP includes master data, audit logs, stock-in, batch barcode/QR generation, label printing, POS sale, sale cancellation, inventory adjustment, reports, live logs, system health, roles, batch upload, a shared dashboard shell, reusable scanner modal, English/Khmer language support, and deployment/backup documentation.

For the latest handoff summary, read `docs/CURRENT_STATUS.md`.

## Quick Start

Copy environment settings:

```bash
cp .env.example .env
```

Edit `.env`, then start the stack:

```bash
docker compose up -d --build
```

For local browser or iPhone testing from a OneDrive-synced workspace, use the local override. It keeps runtime data in Docker volumes and publishes Django directly on port 8000:

```bash
docker compose -f docker-compose.yml -f docker-compose.local.yml up -d --build
```

Run migrations:

```bash
docker compose -f docker-compose.yml -f docker-compose.local.yml exec web python manage.py migrate
```

Collect static files:

```bash
docker compose -f docker-compose.yml -f docker-compose.local.yml exec web python manage.py collectstatic --noinput
```

Create or reset the development admin user:

```bash
docker compose -f docker-compose.yml -f docker-compose.local.yml exec web python manage.py setup_roles --admin-username admin --password Admin123
```

For production with host Nginx, use the production compose file and point host Nginx to `127.0.0.1:${WEB_HOST_PORT}`. Docker runs PostgreSQL, Django, and optional MinIO media storage; host Nginx remains the public reverse proxy.

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

Open:

- Dashboard: http://localhost:8000/dashboard/
- Django Admin: http://localhost:8000/admin/
- Health check: http://localhost:8000/health/
- POS: http://localhost:8000/dashboard/pos/
- Stock-In: http://localhost:8000/dashboard/stock-in/
- Batch Upload: http://localhost:8000/dashboard/batch-upload/
- Reports: http://localhost:8000/dashboard/reports/
- Live Logs: http://localhost:8000/dashboard/live-logs/
- System Health: http://localhost:8000/dashboard/system-health/

## Local Django Commands

If dependencies are installed locally:

```bash
cd app
python manage.py check
python manage.py test
```

## Project Structure

```text
app/
  manage.py
  requirements.txt
  melodu_pos/
  accounts/
  catalog/
  inventory/
  batch_upload/
  pos/
  reports/
  audit/
  system_logs/
  core/
docker/
  django/Dockerfile
data/
  postgres/
  media/
  static/
  logs/
docs/
```

## Important Rule

Implement one phase at a time. Do not start the next phase until the current phase is tested and approved.

## Backups

```bash
scripts/backup_db.sh
scripts/backup_media.sh
scripts/backup_minio.sh
```

See `docs/CURRENT_STATUS.md`, `docs/BACKUP_GUIDE.md`, `docs/BATCH_UPLOAD_GUIDE.md`, `docs/DASHBOARD_UX_GUIDE.md`, `docs/MINIO_STORAGE_GUIDE.md`, and `docs/DEPLOYMENT_GUIDE.md`.
