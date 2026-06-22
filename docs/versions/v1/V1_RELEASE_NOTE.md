# V1 Release Note — MVP POS & Inventory Foundation

## Summary

First production-capable Melodu POS: batch inventory, POS, reports, audit, ops
pages, and deployment baseline. Late V1 added dashboard shell, batch upload, and
scanner support.

## What Changed

- Django monolith with catalog, inventory, POS, reports, audit, system logs
- Melodu Dashboard for daily work
- Batch-level stock with barcode/QR generation
- Six business reports, live logs, system health
- Backup/deployment documentation and scripts

## What Did Not Change

No promotions, fine-grained roles, label templates, OIDC, or multi-store.

## Business Value

Store could sell from real stock batches, trace inventory, and operate without
raw Admin for daily tasks.

## Risk Level

Medium — new system; coarse permissions mitigated by role separation.

## Testing / Verification

Full Django test suite established; browser verification noted in development
log. Production device testing incomplete.

## Known Gaps

UI polish, advanced auth, cost guardrails, label templates — later versions.

## Handoff to Next Version

V2 — stabilize reports, backup/restore, and document baseline before margin work.
