# Data Reset & Admin Maintenance Runbook (V4 Phase 6)

`reset_business_data` safely clears business data for re-launch or to remove
test/demo records. It is an **Owner-level, command-line** operation. There is no
dashboard UI for it (intentionally); a UI would be a separate, approved change.

It **never deletes**: users, roles/StaffProfiles, store settings, label
templates, or audit logs.

## Safety design

- **Dry run by default.** Without `--confirm` it only prints what would be
  deleted.
- **Production guard.** Executing requires the environment variable
  `ALLOW_DATA_RESET=1`. Leave this unset in production except during a planned
  maintenance window.
- **Exact phrase.** Executing requires `--phrase "RESET <scope>"`.
- **Backup acknowledgement.** Executing requires `--backup-confirmed`.
- **Transaction-safe.** All deletions run in one transaction.
- **Audited.** A `DATA_RESET` audit entry is written before (planned) and after
  (deleted) the operation.

## Scopes

| Scope | Deletes | Keeps |
| --- | --- | --- |
| `sales` | Sales, sale items, sale/return movements | Stock, catalog |
| `movements` | All inventory movements | Sales, stock, catalog |
| `batches` | Sales, all movements, stock batches | Catalog (products, etc.) |
| `demo` | Same as `batches` (operational/test data) | Catalog |
| `catalog` | `batches` + promotions, costs, products, tags, categories, brands, suppliers, batch-upload jobs | Users, settings, templates, audit |
| `all` | Same as `catalog` (full business wipe) | Users, settings, templates, audit |

## Procedure

1. **Take a backup first** (always):

   ```bash
   scripts/backup_db.sh
   scripts/backup_media.sh
   ```

2. **Dry run** to review counts (safe anywhere):

   ```bash
   docker compose -f docker-compose.prod.yml exec web \
     python manage.py reset_business_data --scope sales --dry-run
   ```

3. **Execute** during a maintenance window:

   ```bash
   docker compose -f docker-compose.prod.yml exec \
     -e ALLOW_DATA_RESET=1 web \
     python manage.py reset_business_data --scope sales --confirm \
     --phrase "RESET sales" --backup-confirmed
   ```

   For local development replace the compose flags with
   `-f docker-compose.yml -f docker-compose.local.yml`.

## Rollback

There is no undo. If something is wrong, restore from the backup taken in step 1:

```bash
scripts/restore_db.sh <backup-file>
scripts/restore_media.sh <backup-file>
```

See `docs/guides/BACKUP_GUIDE.md`.
