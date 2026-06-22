# V10-001 Multi-store Readiness Audit

Status: Complete
Last updated: 2026-06-16

## Purpose

Identify where the current Melodu POS build assumes one store before any store/location schema is introduced.

## Source Review

| Area | Evidence | Status |
| --- | --- | --- |
| Store identity/settings | `app/core/models.py::StoreSetting` is a singleton forced to `pk=1`. | Current |
| Authentication settings | `app/core/models.py::AuthSetting` is also a singleton. | Current |
| Roles/capabilities | `accounts.Role`, `accounts.StaffProfile`, `core.permissions`, and `core.capabilities` are global, not store-scoped. | Current |
| Product master data | `catalog.Product`, category, brand, supplier, tags, animal types are global. | Current |
| Stock batches | `inventory.StockBatch` has product, supplier, receiver, batch code, quantities, cost, price, status; no store/location field. | Current |
| Inventory movements | `inventory.InventoryMovement` links product and stock batch; no store/location field. | Current |
| Sales | `pos.Sale` and `pos.SaleItem` link cashier/product/stock batch; no store/location field. | Current |
| Promotions | `pos.Promotion` is global by product or category; no store/location field. | Current |
| Label templates | `labels.LabelTemplate` is global; no store/location field. | Current |
| Batch uploads | `batch_upload.BatchUploadJob` is global by target/uploaded user; no store/location field. | Current |
| Audit logs | `audit.AuditLog` records user/action/module/object metadata; no store/location field. | Current |
| Reports | Report views aggregate current global data with no store filters. | Current |
| Deployment | Compose files run one app/database/object-storage stack. | Current |

## Single-store Assumptions

| Assumption | Risk If Multi-store Is Added Later | Risk Level | Follow-up |
| --- | --- | --- | --- |
| There is exactly one store identity and receipt/payment setting row. | Receipts, logos, KHQR, labels, and cost visibility could be wrong per location. | High | V10-006 |
| Inventory stock belongs to the whole business, not a location. | A sale at one location could consume another location's batch. | High | V10-004 |
| Sales are not assigned to a store. | Daily sales, staff sales, closing, and audit review cannot separate locations. | High | V10-005 |
| Staff roles apply globally. | A cashier/manager could access locations they should not manage. | High | V10-003 |
| Promotions and labels are global. | A store-specific price/label campaign cannot be represented safely. | Medium | Future pricing/label scope |
| Audit logs do not carry store context. | Forensics can identify user/object but not location when objects become shared. | Medium | V10-009 |
| Backup/restore assumes one tenant/store stack. | Restore and retention policies may need location-aware operating rules. | Medium | V10-007 |
| Reports have no store selector/filter. | Owner cannot compare locations or isolate one location's closing. | High | V10-005 |

## Boundary Decision

V10 is planning-only for multi-store. No model, migration, permission, route, template, or service behavior is changed by this task.

See `docs/decisions/ADR-0008-multi-store-readiness-boundary.md`.

## Recommended Next Steps

| Step | Status |
| --- | --- |
| Keep current production as single-store until a store/location implementation scope is approved. | Current |
| Use `Store` as the first future concept instead of adding many unrelated location fields ad hoc. | Future / Proposed |
| Plan migration/backfill before adding store foreign keys to stock, sales, audit, reports, and settings. | Future / Proposed |
| Add store-scoped tests before enabling any multi-store UI. | Future / Proposed |

## Verification

Source/documentation audit only. No Django tests were required because no application behavior changed.

