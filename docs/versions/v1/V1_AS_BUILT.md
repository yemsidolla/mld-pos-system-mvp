# V1 As-Built Review — MVP POS & Inventory Foundation

## Summary

V1 delivered a working Django monolith with batch-level inventory, POS, reports,
audit, ops visibility, and deployment baseline. Late V1 added batch upload,
shared dashboard shell, scanner APIs, and dashboard product management.

## Implemented Features

| Feature | Status | Evidence |
| --- | --- | --- |
| Master data models | Implemented | `catalog` migrations, admin |
| Stock-in + `receive_stock()` | Implemented | `inventory/services.py`, Phase 3 log |
| Barcode/QR print page | Implemented | `/dashboard/barcode-print/` |
| POS + receipt | Implemented | `pos` app, Phase 5 log |
| Sales history + cancel | Implemented | Phase 6 log |
| Inventory summary + batch detail | Implemented | Phase 7 log |
| Six reports | Implemented | Phase 8 log |
| Live logs + health | Implemented | Phase 9 log |
| Admin/Cashier permissions | Implemented | Phase 10 log |
| Backup/deploy docs | Implemented | Phase 11 log |
| Batch upload staging | Implemented | 2026-06-08 dev log |
| Dashboard shell + scanner | Implemented | 2026-06-08 dev log |
| Dashboard product CRUD | Implemented | 2026-06-08 dev log |

## Partially Implemented Features

| Feature | Status | Notes |
| --- | --- | --- |
| Mobile scanner UX | Partially Implemented | Modal exists; device matrix Needs Verification |
| Khmer translations | Partially Implemented | i18n wired; completeness Needs Verification |

## Deferred / Not Implemented

Promotions, reference costs, five-role matrix, label templates, OIDC, MinIO,
capability decorators, data reset command.

## Models / Apps / Screens Involved

Apps: `catalog`, `inventory`, `pos`, `audit`, `reports`, `system_logs`, `core`,
`batch_upload`, `accounts`.

Key routes: `/dashboard/`, `/dashboard/pos/`, `/dashboard/stock-in/`,
`/dashboard/inventory/`, `/dashboard/reports/`, `/dashboard/batch-upload/`.

## Permissions / Roles Impact

Initial: `Admin` group (broad access), `Cashier` group (POS + receipts). Cashier
blocked from Django Admin via middleware.

## Data / Migration Impact

Foundational migrations for catalog, inventory, pos, audit. Batch-level stock
model is the permanent foundation (ADR-0003).

## Audit / Logging Impact

`AuditLog` helper, login signals, stock/sale/print actions audited.

## Documentation Impact

`PROJECT_SPEC`, `TASKS`, deployment/backup guides, development log phases 0–11.

## Known Risks

| Risk | Status |
| --- | --- |
| Coarse permissions | Addressed in V4 |
| Internal Docker Nginx confusion | Removed in V1 stabilization |
| LAN HTTP blocks camera on phones | Needs Verification |

## Needs Verification

Exact date boundaries between late V1 features (batch upload vs V2) — classified
as late V1 per development log chronology.

## Handoff to Next Version

V2 should stabilize reports, backup/restore, and document the as-built baseline
before adding margin features.
