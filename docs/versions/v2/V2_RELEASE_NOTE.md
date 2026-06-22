# V2 Release Note — Stabilization, Safety, Reports, and Backup Baseline

## Summary

V2 hardened operations and documented the V1 baseline without major new business
features.

## What Changed

- Baseline audit and supporting docs
- Stock report correctness for sellable inventory
- `expire_batches` maintenance command
- Backup/restore safety improvements
- Dashboard login and access-denied UX
- Catalog quick-create and POS stabilization

## What Did Not Change

Core sale/inventory services, role model (still Admin/Cashier dominant).

## Business Value

Safer operations, clearer documentation, fewer staff dead-ends on dashboard.

## Risk Level

Low — mostly additive docs and targeted UX fixes.

## Testing / Verification

Test suite green at time of delivery; export and restore rehearsal incomplete.

## Handoff to Next Version

V3 — cost control and promotions.
