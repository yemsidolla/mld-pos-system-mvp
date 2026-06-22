# V10-009 Data Retention And Audit Retention Plan

Status: Complete
Last updated: 2026-06-16

## Purpose

Define safe future retention boundaries for business data, logs, backups, media, and audit records. V10 does not delete or archive data.

## Current Data Categories

| Data | Current Behavior | Retention Risk | Status |
| --- | --- | --- | --- |
| Product/catalog master data | Stored until manually changed/deactivated. | Low | Current |
| Stock batches | Stored with quantity/status/expiry/cost/price/code/image data. | High if deleted | Current |
| Inventory movements | Permanent stock history. | High if deleted | Current |
| Sales and sale items | Permanent sales history with cost/promotion snapshots. | High if deleted | Current |
| Audit logs | Permanent application audit trail. | High if deleted | Current |
| Batch upload staging | Upload jobs/rows persist after commit. | Medium | Current |
| Product/store/barcode/QR/media | Stored locally or MinIO depending configuration. | Medium | Current |
| App/error logs | Runtime logs in log files. | Medium | Current |
| Backup archives | Created by scripts; retention schedule requires ops decision. | Needs Verification | Needs Verification |

## Retention Principles

| Principle | Status |
| --- | --- |
| No destructive data cleanup should be added without an owner-approved task. | Current |
| Sales, sale items, stock batches, inventory movements, and audit logs are control records. | Current |
| Retention scripts must support dry-run and clear audit/operator notes if implemented later. | Future / Proposed |
| Backup retention must be defined before automated deletion. | Future / Proposed |
| Media cleanup must not remove barcode/QR/product/store images still referenced by database rows. | Future / Proposed |

## Future Policy Questions

| Question | Status |
| --- | --- |
| How many years must sales records be retained for business/tax needs? | Needs Verification |
| How many years must audit logs be retained? | Needs Verification |
| Should old batch upload staging rows be archived after commit? | Future / Proposed |
| Should app/error logs rotate daily/weekly and for how long? | Needs Verification |
| Where should off-server backups be stored, and for how long? | Needs Verification |
| Who can approve destructive retention actions? | Needs Verification |

## Recommended Future Defaults

These are proposals, not implemented rules:

| Category | Suggested Direction | Status |
| --- | --- | --- |
| Sales/sale items | Keep indefinitely unless a legal/accounting policy says otherwise. | Future / Proposed |
| Inventory movements | Keep indefinitely for stock traceability. | Future / Proposed |
| Audit logs | Keep long-term; never delete without export/archive path. | Future / Proposed |
| App/error logs | Rotate operational logs after a defined window. | Future / Proposed |
| Backups | Keep multiple generations with off-server copy. | Future / Proposed |
| Upload staging | Consider archive/cleanup only after commit summary and audit evidence remain available. | Future / Proposed |

## Verification

Planning-only. No deletion, archival, retention job, management command, or script change was made.

