# V3 As-Built Review — Cost Control, Pricing Rules, and Promotion Foundation

## Summary

V3 added reference costs, batch actual/landed costs, promotion model, below-cost
guardrails with override, SaleItem snapshots, responsive POS, multi-animal
products, and optional MinIO.

## Implemented Features

| Feature | Status |
| --- | --- |
| `/dashboard/reference-costs/` | Implemented |
| Batch `actual_unit_cost`, `landed_unit_cost` | Implemented |
| `Promotion` CRUD at `/dashboard/promotions/` | Implemented |
| Below-cost block for cashier; override for authorized roles | Implemented |
| Promotion price in POS via `choose_best_promotion` | Implemented |
| Cost/promotion audit actions | Implemented |
| `AnimalTypeOption` + product M2M | Implemented |
| `USE_S3_MEDIA` + MinIO compose | Implemented |

## Partially Implemented Features

| Feature | Status |
| --- | --- |
| Khmer POS strings | Needs Verification |
| MinIO production cutover | Needs Verification |

## Deferred

Refunds, complex promotion campaigns, accounting exports.

## Models / Apps

`catalog` (SupplierProductCost, AnimalTypeOption), `inventory` (cost fields),
`pos` (Promotion, SaleItem snapshots), `core` (media storage settings).

## Handoff to Next Version

V4 — five roles, classification polish, printing, reset tooling.
