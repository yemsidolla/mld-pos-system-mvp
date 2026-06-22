# ADR-0003: Batch-Level Inventory

Status: Accepted
Date: 2026-06-16

## Context

Melodu sells pet-store stock where expiry, supplier, cost, selling price, and barcode/QR labels matter. Product master data alone cannot represent sellable inventory safely.

## Decision

`StockBatch` is the sellable stock unit. `Product` remains master data. Every `SaleItem` must link to a `StockBatch`, and every stock change must create an `InventoryMovement`. Critical stock actions must also create `AuditLog` records.

## Consequences

| Consequence | Status |
| --- | --- |
| Sales can reverse stock to the exact original batch. | Current |
| Expiry and cost can be tracked per received batch. | Current |
| Stock-in, sale, cancellation, and adjustment workflows must use transactions. | Current |
| Import and UI workflows must not bypass inventory services. | Current |
| Stock must never go negative. | Current |

## Alternatives Considered

| Alternative | Decision |
| --- | --- |
| Product-level stock count only | Outdated; insufficient for expiry, cost, and reversal control. |
| Supplier-level stock without batches | Outdated; insufficient for label and expiry workflows. |
| Manual spreadsheet inventory | Outdated; no reliable audit trail. |

## Review Trigger

Review this ADR only if the store adopts a fundamentally different inventory model, such as warehouse transfers, serial-number inventory, or multi-store fulfillment.
