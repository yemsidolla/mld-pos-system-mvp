# V10-002 Store / Location Model Plan

Status: Complete
Last updated: 2026-06-16

## Purpose

Define the future store/location data-model direction without applying migrations now.

## Current Reality

| Model Area | Current Store Awareness | Status |
| --- | --- | --- |
| `StoreSetting` | Singleton store identity, receipt, KHQR, quick keys, and cost visibility settings. | Current |
| `AuthSetting` | Singleton authentication runtime settings. | Current |
| `Product`, `Category`, `Brand`, `Supplier` | Global master data. | Current |
| `StockBatch`, `InventoryMovement` | Global inventory. | Current |
| `Sale`, `SaleItem` | Global sales. | Current |
| `AuditLog` | Global audit trail. | Current |
| `LabelTemplate`, `Promotion` | Global operational configuration. | Current |

## Proposed Direction

Start with a single `Store` concept representing a sellable operating location. Do not introduce both `Store` and `Warehouse` until a transfer/warehouse requirement is approved.

| Future Concept | Proposed Responsibility | Status |
| --- | --- | --- |
| `Store` | Store name, code, active status, address/contact, default currency/display settings linkage. | Future / Proposed |
| Default store row | Backfills current single-store data to one store, likely `Melodu Pet Store`. | Future / Proposed |
| Store-scoped stock | `StockBatch` and `InventoryMovement` carry store. | Future / Proposed |
| Store-scoped sale | `Sale` carries store; `SaleItem` remains linked to a batch that must belong to the same store. | Future / Proposed |
| Store-scoped settings | Receipt/logo/KHQR/quick keys can be separated per store. | Future / Proposed |
| Store-aware audit | `AuditLog` carries optional store for future traceability. | Future / Proposed |

## Recommended Attachment Rules

| Data | Recommendation | Reason |
| --- | --- | --- |
| Category/brand/product tags/animal types | Stay global at first. | Avoid duplicate catalog maintenance. |
| Product | Stay global at first; use store-scoped stock/price only if approved. | Current product code/barcode rules are global and stable. |
| Supplier | Stay global at first. | A supplier can serve multiple stores. |
| Supplier product costs | Needs Verification. | Costs may differ by store, supplier branch, or contract. |
| Stock batch | Add store when multi-store is implemented. | Batch is the sellable inventory unit. |
| Inventory movement | Add store and validate against batch store. | Movement traceability must match batch ownership. |
| Sale | Add store and validate all line batches match sale store. | Prevent cross-location stock deduction. |
| Promotion | Future decision. | Campaigns may be global or store-specific. |
| Label template | Future decision. | Some labels are global; printer/paper setups may differ by store. |
| Audit log | Add optional store. | Preserve traceability for shared/global objects. |

## Migration Sequence Proposal

| Step | Status |
| --- | --- |
| Create `Store` with one default active row. | Future / Proposed |
| Backfill store onto `StockBatch`, `InventoryMovement`, and `Sale`. | Future / Proposed |
| Add database constraints/service validation for matching sale/batch store. | Future / Proposed |
| Add store-aware permission model before exposing store selectors. | Future / Proposed |
| Add report filters and defaults after data scoping exists. | Future / Proposed |
| Split `StoreSetting` only after receipt/payment/quick-key migration is designed. | Future / Proposed |

## Out Of Scope

- Warehouse transfers.
- Franchise/tenant isolation.
- Per-store database split.
- Public API integration.
- Store-specific accounting.

## Verification

Planning-only. No schema changes, migrations, or tests were added.

