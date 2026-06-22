# V10-007 Deployment And Backup Hardening Review

Status: Complete
Last updated: 2026-06-16

## Purpose

Review production-readiness around deployment, backup, restore, and reset safety before scale changes.

## Current Evidence

| Area | Evidence | Status |
| --- | --- | --- |
| Local compose | `docker-compose.yml` defines app stack with PostgreSQL and MinIO support. | Current |
| Production compose | `docker-compose.prod.yml` supports production deployment shape. | Current |
| Host Nginx | Production currently uses host Nginx outside Docker. | Current |
| Database backup | `scripts/backup_db.sh`; documented in `docs/guides/BACKUP_GUIDE.md`. | Current |
| Media backup | `scripts/backup_media.sh`; documented. | Current |
| MinIO backup | `scripts/backup_minio.sh`; documented in MinIO guide. | Current |
| Restore scripts | `scripts/restore_db.sh`, `restore_media.sh`, `restore_minio.sh`. | Current |
| Deployment runbook | `docs/operations/DEPLOYMENT_RUNBOOK.md`. | Mostly Current |
| Reset runbook | `docs/operations/RESET_ADMIN_RUNBOOK.md`. | Current |
| Dashboard visibility | System Health shows backup command/runbook references after V9. | Current |

## Hardening Gaps

| Gap | Status | Recommendation |
| --- | --- | --- |
| Restore rehearsal evidence is not recorded in docs. | Needs Verification | Add a non-production restore rehearsal checklist before scale release. |
| Host Nginx config is operationally important but not fully managed by compose. | Current | Keep host Nginx runbook examples current, including CSRF/trusted-origin notes. |
| Backup retention schedule needs owner decision. | Needs Verification | Define daily/weekly/monthly retention in V10-009 or later ops task. |
| Off-server backup destination is not guaranteed by repo scripts alone. | Needs Verification | Add VPS/cloud storage SOP if the owner approves. |
| Secrets/environment backup handling needs explicit safety notes. | Needs Verification | Document that `.env` is sensitive and not committed. |

## Recommended Production Checklist Before Scale Implementation

- Confirm `docker compose pull/build` and migration steps are documented for the active deployment mode.
- Rehearse database restore to a non-production database.
- Rehearse media/MinIO restore to a non-production bucket/path.
- Confirm static/media URLs work behind host Nginx.
- Confirm HTTPS, proxy headers, allowed hosts, and CSRF trusted origins.
- Confirm backup files are encrypted or stored in a restricted location.
- Confirm reset scripts are owner-only and never exposed as dashboard buttons.

## What Did Not Change

- No compose file was changed.
- No script was changed.
- No backup/restore command behavior was changed.
- No reset behavior was changed.

## Verification

Documentation review only. Script execution or restore rehearsal should happen in a separate ops task with a non-production target.

