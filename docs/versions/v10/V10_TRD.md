# V10 Technical Requirements

Status: Complete (Planning Only)
Last updated: 2026-06-16

## Planning Focus

| Area | Question |
| --- | --- |
| Data model | How would `Store` or `Location` attach to batches and sales? |
| Auth | Per-store roles vs global owner? |
| Inventory | Single DB multi-tenant vs per-store isolation? |
| Reporting | Aggregated vs per-store dashboards? |
| Deployment | Same monolith, stronger ops boundaries? |

## Constraints

- ADR-0001 Django monolith remains default
- No implementation without ADR for multi-store schema
- Current production: single store (`https://melodu-pos.khlovepet.com`)

## Deliverables

Architecture notes, ADR-0008, backlog/tracker updates, and V10 evidence docs. No production schema, permission, route, template, report, or service behavior changed.

See `V10_TASKS.md`.

## Evidence Docs

- `V10_MULTI_STORE_READINESS_AUDIT.md`
- `V10_STORE_LOCATION_MODEL_PLAN.md`
- `V10_STORE_LEVEL_PERMISSION_PLAN.md`
- `V10_STORE_LEVEL_INVENTORY_PLAN.md`
- `V10_STORE_LEVEL_REPORTING_PLAN.md`
- `V10_STORE_SETTINGS_SEPARATION_REVIEW.md`
- `V10_DEPLOYMENT_BACKUP_HARDENING_REVIEW.md`
- `V10_MONITORING_LOGGING_SCALE_READINESS.md`
- `V10_DATA_RETENTION_AUDIT_RETENTION_PLAN.md`
- `V10_PERFORMANCE_DATABASE_REVIEW.md`
