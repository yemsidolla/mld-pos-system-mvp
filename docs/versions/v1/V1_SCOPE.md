# V1 Scope — MVP POS & Inventory Foundation

## Status

Historical / Completed

## Version Goal

Build the first usable Melodu POS and batch-level inventory control system on a
Django monolith with PostgreSQL, Docker Compose, and a Melodu Dashboard for
daily retail operations.

## Why This Version Existed

Melodu Pet Store needed a controlled replacement for ad-hoc spreadsheets and raw
Django Admin workflows. V1 established sellable stock as batches, traceable
movements, POS sales, and operational visibility.

## In Scope

| Area | Status |
| --- | --- |
| Django monolith, PostgreSQL, Docker Compose, Gunicorn, WhiteNoise | Implemented |
| Host/external Nginx HTTPS reverse proxy (not internal Docker Nginx) | Implemented |
| Django Admin + Melodu Dashboard | Implemented |
| Catalog master data (category, brand, supplier, product) | Implemented |
| `StockBatch` as sellable stock unit | Implemented |
| `InventoryMovement` ledger | Implemented |
| Stock-in with batch number, custom code, barcode/QR images | Implemented |
| POS sale flow with `SaleItem` → `StockBatch` | Implemented |
| Receipt at `/dashboard/pos/receipt/<id>/` | Implemented |
| Sale cancellation with stock reversal | Implemented |
| Inventory adjustment, damage, expiry handling | Implemented |
| Six HTML reports | Implemented |
| `AuditLog` for critical actions | Implemented |
| Live logs and system health | Implemented |
| Admin/Cashier role baseline | Implemented |
| Production deployment and backup scripts/docs | Implemented |
| Late V1: batch upload, dashboard shell, scanner, i18n, product CRUD | Implemented |

## Out Of Scope

Advanced UI polish, Authentik/OIDC, capability matrix, label templates,
promotions, multi-store, SaaS readiness.

## Source Evidence

- `docs/DEVELOPMENT_LOG.md` — Phases 0–11 (2026-06-06), V1 stabilization and
  dashboard work (2026-06-08)
- `docs/reference/PROJECT_SPEC.md` — Phase 0–11 baseline
- `docs/legacy/V2_BASELINE_AUDIT.md` — V1 maturity assessment

## Major Modules Affected

`catalog`, `inventory`, `pos`, `audit`, `reports`, `system_logs`, `core`,
`batch_upload` (late V1), `accounts` (basic roles)

## Success Criteria

| Criterion | Status |
| --- | --- |
| Cashier can complete a sale from dashboard | Implemented |
| Stock cannot go negative in normal workflows | Implemented |
| Stock changes create movement rows | Implemented |
| Critical actions are auditable | Implemented |
| Deployment/backup documented | Implemented |

## Known Gaps

| Gap | Status |
| --- | --- |
| Dashboard UX was functional but not polished | Deferred → V5/V7 |
| Permissions were coarse (Admin/Cashier) | Deferred → V4/V6 |
| No promotions or cost guardrails | Deferred → V3 |
| Report export | Deferred → V2 backlog |

## What Later Versions Should Improve

V2 stabilization, V3 cost/promotions, V4 roles/labels/classification, V5 UI
polish, V6 documentation and OIDC.
