# Backup Guide

Version 1 uses local VPS backups. If Garage media storage is enabled, back up
`data/garage` instead of only `data/media`.

## What To Back Up

- PostgreSQL database: required.
- `data/media`: required when `USE_S3_MEDIA=False`.
- `data/garage`: required when `USE_S3_MEDIA=True` because barcode, QR, store,
  KHQR, and product images are stored there.
- `data/logs`: optional for troubleshooting history.
- `data/static`: can be regenerated with `collectstatic`.

## Create Database Backup

```bash
scripts/backup_db.sh
```

The script writes a SQL dump under `backups/`.

By default the script uses `docker-compose.prod.yml`. For local Docker volume testing, run:

```bash
COMPOSE_FILE=docker-compose.yml:docker-compose.local.yml scripts/backup_db.sh
```

## Create Media Backup

```bash
scripts/backup_media.sh
```

The script writes a compressed archive under `backups/`.

By default the script archives `data/media`. Override the source when needed:

```bash
MEDIA_SOURCE=data/media scripts/backup_media.sh
```

## Create Garage Backup

Garage must be stopped for a consistent archive. A hot tar of `data/garage`
while Garage is running can capture torn metadata.

```bash
# Script stops Garage, archives, then restarts it
GARAGE_BACKUP_STOP=yes scripts/backup_garage.sh
```

Or stop/start yourself:

```bash
docker compose stop garage
scripts/backup_garage.sh
docker compose start garage
```

If Garage is running and `GARAGE_BACKUP_STOP` is not `yes`, the script refuses
to run.

The script archives `data/garage` by default. Override the source when needed:

```bash
GARAGE_SOURCE=data/garage GARAGE_BACKUP_STOP=yes scripts/backup_garage.sh
```

By default the script uses `docker-compose.yml`. For local or production compose
files:

```bash
COMPOSE_FILE=docker-compose.yml:docker-compose.local.yml GARAGE_BACKUP_STOP=yes scripts/backup_garage.sh
COMPOSE_FILE=docker-compose.prod.yml GARAGE_BACKUP_STOP=yes scripts/backup_garage.sh
```
## Restore Database

```bash
CONFIRM_RESTORE=yes scripts/restore_db.sh backups/melodu_pos_db_YYYYMMDD_HHMMSS.sql
```

Restore into a clean or intentionally replaceable database. Confirm the target `.env` points to the correct PostgreSQL service before running restore.

## Restore Media

```bash
CONFIRM_RESTORE=yes scripts/restore_media.sh backups/melodu_pos_media_YYYYMMDD_HHMMSS.tar.gz
```

## Restore Garage

Stop the Garage container before restoring. The restore script refuses if Garage
is running, moves the existing `data/garage` aside (no merge into a live or
stale directory), then extracts the archive:

```bash
docker compose stop garage
CONFIRM_RESTORE=yes scripts/restore_garage.sh backups/melodu_pos_garage_YYYYMMDD_HHMMSS.tar.gz
docker compose start garage
```

Previous data is left at `data/garage.before_restore_YYYYMMDD_HHMMSS` when a
prior directory existed.

## Recommended Schedule

- Database: daily.
- Media/Garage: weekly, and immediately after large product or stock-label updates.
- Restore rehearsal: monthly on a non-production copy.
- Keep at least 7 daily database backups and 4 weekly media backups.
