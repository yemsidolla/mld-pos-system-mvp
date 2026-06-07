# Backup Guide

Version 1 uses local VPS backups.

## What To Back Up

- PostgreSQL database: required.
- `data/media`: required because barcode, QR, and product images are stored there.
- `data/logs`: optional for troubleshooting history.
- `data/static`: can be regenerated with `collectstatic`.

## Create Database Backup

```bash
scripts/backup_db.sh
```

The script writes a SQL dump under `backups/`.

## Create Media Backup

```bash
scripts/backup_media.sh
```

The script writes a compressed archive under `backups/`.

## Restore Database

```bash
scripts/restore_db.sh backups/melodu_pos_db_YYYYMMDD_HHMMSS.sql
```

Restore into a clean or intentionally replaceable database. Confirm the target `.env` points to the correct PostgreSQL service before running restore.

## Restore Media

```bash
tar -xzf backups/melodu_pos_media_YYYYMMDD_HHMMSS.tar.gz
```

## Recommended Schedule

- Database: daily.
- Media: weekly, and immediately after large product or stock-label updates.
- Keep at least 7 daily database backups and 4 weekly media backups.
