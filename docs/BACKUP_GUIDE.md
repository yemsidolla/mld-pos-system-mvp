# Backup Guide

Version 1 uses local VPS backups. If MinIO media storage is enabled, back up
`data/minio` instead of only `data/media`.

## What To Back Up

- PostgreSQL database: required.
- `data/media`: required when `USE_S3_MEDIA=False`.
- `data/minio`: required when `USE_S3_MEDIA=True` because barcode, QR, store,
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

## Create MinIO Backup

```bash
scripts/backup_minio.sh
```

The script archives `data/minio` by default. Override the source when needed:

```bash
MINIO_SOURCE=data/minio scripts/backup_minio.sh
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

## Restore MinIO

```bash
CONFIRM_RESTORE=yes scripts/restore_minio.sh backups/melodu_pos_minio_YYYYMMDD_HHMMSS.tar.gz
```

## Recommended Schedule

- Database: daily.
- Media/MinIO: weekly, and immediately after large product or stock-label updates.
- Restore rehearsal: monthly on a non-production copy.
- Keep at least 7 daily database backups and 4 weekly media backups.
