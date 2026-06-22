# V10-004 Store-level Inventory Plan

Status: Complete
Last updated: 2026-06-16

## Purpose

Plan how batch-level inventory would become store-aware while preserving the core rule: `StockBatch` is the sellable stock unit.

## Current Inventory Model

| Workflow/Data | Current Behavior | Status |
| --- | --- | --- |
| Product | Master data only. | Current |
| Stock batch | Sellable stock unit with quantity, expiry, costs, selling price, custom code, barcode, QR, status. | Current |
| Inventory movement | Created for stock changes and linked to product/batch. | Current |
| Stock-in | Uses `receive_stock()` service and creates batch, movement, barcode/QR, audit. | Current |
| Sale | Deducts from selected stock batch through POS sale service. | Current |
| Cancellation/adjustment | Reverses or changes stock with movement/audit. | Current |
| Store awareness | None. | Missing |

## Future Store Rules

| Rule | Status |
| --- | --- |
| Every sellable stock batch belongs to exactly one store. | Future / Proposed |
| Every inventory movement belongs to the same store as its stock batch. | Future / Proposed |
| Every sale belongs to exactly one store. | Future / Proposed |
| Every sale item must use a batch from the same store as the sale. | Future / Proposed |
| Stock lookup in POS must filter to the selected/authorized store. | Future / Proposed |
| Stock-in must receive into a selected/authorized store. | Future / Proposed |
| Original barcode lookup may find a global product, but batch selection must be store-filtered. | Future / Proposed |
| Melodu custom code lookup should select an exact batch and therefore an exact store. | Future / Proposed |

## Transfer Boundary

Store-to-store transfers are not part of V10. If approved later, they need a dedicated service and movement design:

| Transfer Requirement | Status |
| --- | --- |
| Source store stock decreases transactionally. | Future / Proposed |
| Destination store stock increases transactionally. | Future / Proposed |
| Both movement records share a transfer reference. | Future / Proposed |
| Transfer cancellation/reversal rules are documented. | Future / Proposed |
| Audit records identify source, destination, user, and reason. | Future / Proposed |

## Migration Risks

| Risk | Mitigation |
| --- | --- |
| Backfilling existing global batches to a store could be wrong if historical data mixed locations. | Confirm production is single-store before migration. |
| POS could sell from an unauthorized or wrong-store batch. | Add service-level validation and tests, not only UI filtering. |
| Reports could double-count if store joins are added incorrectly. | Add report regression tests before release. |
| Barcode/label pages could print labels for another store. | Filter by authorized store and show store context. |

## Future Test Requirements

- Stock-in creates a batch for the selected store only.
- Sale cannot use a batch from another store.
- Adjustment cannot edit another store's batch.
- Low-stock/expiry reports respect store filters.
- Inventory movement ledger can filter by store.
- Owner can view all stores when explicitly selected.

## Verification

Planning-only. No inventory schema or service changes were made.

