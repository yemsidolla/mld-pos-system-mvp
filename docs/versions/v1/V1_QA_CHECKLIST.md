# V1 QA Checklist — MVP POS & Inventory Foundation

## Purpose

Historical QA focus for the V1 MVP baseline.

## Functional Checks

- [x] Stock-in creates batch, movement, audit, barcode/QR — Implemented
- [x] POS deducts from selected batch; receipt renders — Implemented
- [x] Sale cancel restores original batch — Implemented
- [x] Reports render for admin — Implemented
- [x] Batch upload preview/commit for supported targets — Implemented

## Permission Checks

- [x] Cashier reaches POS; blocked from admin-only pages — Implemented
- [x] Cashier blocked from Django Admin — Implemented

## Data Safety Checks

- [x] Negative stock prevented — Implemented
- [x] SaleItem requires StockBatch link — Implemented

## UI/UX Checks

- [ ] Mobile scanner on production phones — Needs Verification
- [x] Dashboard shell on major pages — Implemented

## Report Checks

- [x] Daily sales, stock, low stock, expiry, movements, staff sales — Implemented

## Printing Checks

- [x] Barcode/QR browser print — Implemented

## Audit Checks

- [x] Login, stock-in, sale, print actions logged — Implemented

## Deployment Checks

- [x] `docker-compose.prod.yml`, backup scripts — Implemented
- [ ] Production HTTPS smoke test — Needs Verification

## Known Missing QA

Formal device matrix, restore rehearsal, export formats.

## Regression Risks for Future Versions

Batch-level inventory rules, movement ledger, and audit trail must not break in
any later version.
