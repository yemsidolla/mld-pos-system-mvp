# V3 Scope — Cost Control, Pricing Rules, and Promotion Foundation

## Status

Historical / Completed

## Version Goal

Protect margin with real cost data, below-cost guardrails, and simple promotions
while improving POS responsiveness.

## Why This Version Existed

V1/V2 handled stock and sales; owners needed cost visibility, margin protection,
and promotional pricing without a complex promotion engine.

## In Scope

| Area | Status |
| --- | --- |
| Supplier/product reference costs | Implemented |
| `actual_unit_cost` + optional `landed_unit_cost` on batches | Implemented |
| Cost basis priority for sale validation | Implemented |
| SaleItem cost/price snapshots at sale time | Implemented |
| Below-cost blocking + admin override with reason | Implemented |
| `Promotion` model (%, fixed amount, fixed price) | Implemented |
| Best single promotion per product; no stacking | Implemented |
| `allow_below_cost` on promotions | Implemented |
| Responsive POS improvements | Implemented |
| Multi-animal product types | Implemented |
| Optional MinIO media storage | Implemented |

## Out Of Scope

Purchase orders, loyalty, coupons, stacked promotions, accounting integration,
refund workflow, multi-branch cost.

## Source Evidence

- `docs/legacy/V3_PHASE_1_COST_GUARDRAILS_PROMOTIONS_POS.md`
- `docs/DEVELOPMENT_LOG.md` — V3 Phase 1, catalog fixes, MinIO
- `app/pos/pricing.py`, `app/pos/services.py`

## Cost Priority (verified in code)

1. `landed_unit_cost` when present on batch
2. Else `actual_unit_cost` when > 0
3. Else supplier/product reference cost
4. Else product default cost

Implemented in `app/pos/pricing.py` (`cost_basis` selection).

## Known Gaps

| Gap | Status |
| --- | --- |
| Refund workflow | Deferred — model enum only |
| MinIO migration of existing media | Needs Verification |

## What Later Versions Should Improve

V8 promotion professionalization, V9 cost/below-cost reporting.
