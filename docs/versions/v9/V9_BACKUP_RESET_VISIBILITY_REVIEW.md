# V9-010 Backup And Reset Visibility Review

Status: Complete
Last updated: 2026-06-16

## Purpose

Make backup and reset posture easier to find without weakening safety controls.

## Source Review

| Area | Evidence | Status |
| --- | --- | --- |
| Database backup | `scripts/backup_db.sh`, `docs/guides/BACKUP_GUIDE.md` | Current |
| Media backup | `scripts/backup_media.sh`, `docs/guides/BACKUP_GUIDE.md` | Current |
| MinIO backup | `scripts/backup_minio.sh`, `docs/guides/MINIO_STORAGE_GUIDE.md` | Current |
| Restore guards | `CONFIRM_RESTORE=yes` in restore scripts | Current |
| Data reset guards | `ALLOW_DATA_RESET=1`, exact phrase, backup acknowledgement, dry-run-first, audited command | Current |
| Dashboard reset button | Intentionally absent | Current |

## Implementation

- Updated `app/system_logs/views.py`.
- Updated `app/templates/system_logs/system_health.html`.
- Updated `app/system_logs/tests.py`.

## What Changed

- Added Backup / Reset Safeguards panel to System Health.
- Listed backup command names and runbook paths.
- Stated clearly that reset remains command-line only and has no dashboard button.

## What Did Not Change

- No backup script behavior changed.
- No restore script behavior changed.
- No reset command behavior changed.
- No dashboard execution path was added for backup, restore, or reset.
- No database migrations were introduced.

## Verification

```bash
docker compose run --rm --no-deps -v "$PWD/app:/app" web python manage.py test system_logs.tests.SystemLogTests --noinput --verbosity 1
```

Result: 6 tests OK.
