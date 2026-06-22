# V3 Release Note — Cost Control, Pricing Rules, and Promotion Foundation

## Summary

V3 made Melodu POS margin-aware: real costs on batches, reference costs,
below-cost protection, and simple promotions with audit evidence.

## What Changed

- Reference costs and batch actual/landed costs
- SaleItem snapshots preserve cost/price at sale time
- Promotions (%, fixed amount, fixed price) in POS
- Below-cost override with reason for authorized users
- Multi-animal products; optional MinIO media

## What Did Not Change

Batch-level inventory truth, no refund UI, no payment gateway.

## Business Value

Owners can track margin, block cashier mistakes, and run simple promos.

## Risk Level

Medium — pricing logic affects revenue; covered by extensive `pos` tests.

## Testing / Verification

Full test suite at delivery; MinIO production — Needs Verification.

## Handoff to Next Version

V4 — roles, classification, receipts, labels, reset.
