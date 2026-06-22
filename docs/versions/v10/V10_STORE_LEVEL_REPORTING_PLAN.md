# V10-005 Store-level Reporting Plan

Status: Complete
Last updated: 2026-06-16

## Purpose

Plan how reports should behave when store/location data exists.

## Current Report Behavior

| Report | Current Scope | Status |
| --- | --- | --- |
| Daily Sales | All sales for selected date. | Current |
| Staff Sales | All-time cashier aggregation. | Current |
| Promotion & Below-cost | Completed sale-item snapshots, all stores because no store exists. | Current |
| Stock Summary | Global active products and sellable batch quantities. | Current |
| Low Stock | Global active products below minimum stock. | Current |
| Expiry | Global active batches expiring/expired. | Current |
| Stock Movements | Global movement ledger with filters. | Current |
| Daily Closing Checklist | Links to global report evidence. | Current |
| Audit Logs | Global audit list with filters. | Current |

## Future Store Reporting Rules

| Rule | Status |
| --- | --- |
| Store selector appears only after store-scoped data and permissions exist. | Future / Proposed |
| Users see only stores assigned by permission, except Owner/global manager. | Future / Proposed |
| Owner can view one store or all stores where aggregation is meaningful. | Future / Proposed |
| Daily closing should default to one store, one business date. | Future / Proposed |
| Stock, low-stock, expiry, and movements should default to the selected store. | Future / Proposed |
| Staff sales should group by store and cashier when more than one store is selected. | Future / Proposed |
| Audit logs should support store filter if audit records carry store context. | Future / Proposed |

## Report Dependencies

| Report | Required Future Store Field | Notes |
| --- | --- | --- |
| Daily Sales | `Sale.store` | Payment breakdown and completed/cancelled split filter by sale store. |
| Staff Sales | `Sale.store`, possibly staff-store assignment | Must avoid cross-store staff leakage. |
| Promotion & Below-cost | `Sale.store` and optionally `Promotion.store` | Historical sale-item snapshots remain source of truth. |
| Stock Summary | `StockBatch.store` | Product master data can stay global. |
| Low Stock | `StockBatch.store` | Minimum stock may need store-specific values later. |
| Expiry | `StockBatch.store` | Store-filtered expiry review. |
| Stock Movements | `InventoryMovement.store` or batch store join | Ledger should not require expensive joins forever. |
| Closing Checklist | `Sale.store`, stock/report filters, system checks | Closing should become store-specific before final close records. |

## UI Direction

Future store filters must follow `docs/DESIGN_SYSTEM.md`. The likely pattern is a compact report filter row with:

- Business date or date range.
- Store selector, hidden when only one store is available.
- Clear active filter summary.
- Export/print controls only after the report data is correct.

## Future Test Requirements

- Report user cannot access unauthorized store data.
- Owner all-store report totals equal the sum of individual store totals.
- Daily closing links preserve selected store/date.
- Store filters do not change completed/cancelled sale definitions.
- Cost/margin visibility remains gated after store filtering.

## Verification

Planning-only. No report behavior changed.

