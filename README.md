# Melodu POS & Inventory Control System

Melodu Store Control System — role-based POS and inventory for Melodu Pet Store.

**Production:** https://melodu-pos.khlovepet.com

Django monolith · PostgreSQL · Docker Compose · Gunicorn · WhiteNoise · optional Garage · optional Authentik/OIDC

## Current Status

The V1 MVP core is implemented: dashboard POS, batch-level inventory, catalog,
batch upload, labels, promotions, reports, audit, roles/capabilities, and
optional OIDC. V7, V8, and V9 are complete, and V10 is complete as a planning
package for future multi-store/scale readiness. Multi-store behavior is not
implemented yet.

Handoff: `docs/CURRENT_STATUS.md` · System map: `docs/product/00_CURRENT_SYSTEM_MAP.md`

## Standard Way Of Working

**Before any new work**, read `docs/STANDARD_WAY_OF_WORKING.md`.

## Documentation

| Doc | Purpose |
| --- | --- |
| `docs/README.md` | Docs folder index |
| `docs/product/11_DOCUMENTATION_MAP.md` | Read order and authority |
| `docs/product/08_VERSION_ROADMAP.md` | V1–V10 roadmap (historical + future) |
| `docs/versions/v1/`–`v5/` | Historical version docs |
| `docs/product/09_IMPLEMENTATION_BACKLOG.md` | Task backlog |
| `docs/versions/VERSION_COMPLETION_TRACKER.md` | Version completion |
| `docs/DESIGN_SYSTEM.md` | UI authority |

## Architecture Summary

- Django 5.2 monolith with Django templates and vanilla JS
- PostgreSQL 16, Docker Compose, host Nginx for production HTTPS
- Batch-level inventory (`StockBatch` is sellable stock)
- Role + capability authorization
- Local login default; Authentik/OIDC optional

## Quick Start

```bash
cp .env.example .env
docker compose -f docker-compose.yml -f docker-compose.local.yml build
docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm web python manage.py migrate
docker compose -f docker-compose.yml -f docker-compose.local.yml up -d
docker compose -f docker-compose.yml -f docker-compose.local.yml exec web python manage.py setup_roles --admin-username admin --password Admin123
```

**Local URLs:**

- Mac: http://127.0.0.1:8000/dashboard/
- LAN/iPhone: http://192.168.1.199:8000/dashboard/ (adjust to your host IP)

## Development Commands

```bash
cd app && python manage.py check && python manage.py test
```

Or with Docker:

```bash
docker compose -f docker-compose.yml -f docker-compose.local.yml exec web python manage.py test
```

## Deployment

Production compose: `docker-compose.prod.yml`. See `docs/guides/DEPLOYMENT_GUIDE.md`.

## Backups

```bash
scripts/backup_db.sh
scripts/backup_media.sh
scripts/backup_garage.sh
```

See `docs/guides/BACKUP_GUIDE.md`.

## Important Rule

Follow `docs/STANDARD_WAY_OF_WORKING.md` before planning or implementing new work.
Do not start future implementation from planning docs alone; use the completion
tracker and create an approved task first.

## Project Structure

```text
app/          Django apps (accounts, catalog, inventory, pos, …)
docs/         Product foundation, versions, guides, ADRs
docker/       Container build files
scripts/      Backup/restore scripts
```
