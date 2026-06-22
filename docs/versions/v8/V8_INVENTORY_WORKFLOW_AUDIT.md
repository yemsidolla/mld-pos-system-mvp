# V8 Inventory Workflow Audit

Status: Complete
Last updated: 2026-06-16

## Scope

This audit covers the current stock-in, stock overview, batch detail, adjustment, damage, expiry, maintenance expiry command, reports, movement ledger, audit logging, and inventory permission flow.

## Source Reviewed

| Area | Source | Status |
| --- | --- | --- |
| Stock-in service | `app/inventory/services.py` | Current |
| Stock-in form/page | `app/inventory/forms.py`, `app/inventory/views.py`, `app/templates/inventory/stock_in.html` | Current |
| Stock overview | `app/inventory/views.py`, `app/templates/inventory/inventory_summary.html` | Mostly Current |
| Batch detail/actions | `app/templates/inventory/stock_batch_detail.html` | Mostly Current |
| Expiry command | `app/inventory/management/commands/expire_batches.py` | Current |
| Reports | `app/reports/views.py`, `app/templates/reports/*.html` | Mostly Current |
| Permissions/cost visibility | `app/core/permissions.py`, `app/core/context_processors.py` | Current |
| Tests | `app/inventory/tests.py`, `app/reports/tests.py`, `app/core/tests_cost_visibility.py` | Current |

## Confirmed Controls

| Control | Finding | Status |
| --- | --- | --- |
| Batch-level stock-in | `receive_stock()` always creates a new `StockBatch` and does not update product master stock. | Current |
| Transaction protection | Stock-in, adjustment, damaged stock, and expiry actions are wrapped in database transactions. | Current |
| Negative stock prevention | Adjustment and damaged stock flows reject quantities that would reduce stock below zero. | Current |
| Barcode/QR generation | Stock-in generates Code128 barcode and QR image from the Melodu custom batch code. | Current |
| Movement ledger | Stock-in, adjustment, damage, and expiry services create `InventoryMovement`. | Current |
| Audit logging | Stock-in, cost snapshot, adjustment, damage, and expiry actions create `AuditLog` records. | Current |
| Expiry maintenance | `expire_batches` uses `mark_batch_expired()` so movements and audit logs are preserved. | Current |
| Cost visibility | Batch detail hides actual/landed costs unless `can_view_costs()` allows the user. | Current |

## Workflow Gaps Found

| Gap | Impact | Follow-up Task | Status |
| --- | --- | --- | --- |
| Stock overview lists batches but does not show supplier, received quantity, expiry urgency label, cost-safe price context, or direct print/report links in one place. | Managers need extra clicks to understand batch condition. | V8-002 | In Scope |
| Product summary shows total availability but not sellable-only context, low-stock gap, or next action. | Staff may not know whether to receive stock or review expiring batches. | V8-003 | In Scope |
| Batch detail has safe service actions, but movement history is not shown next to the batch actions. | Traceability requires jumping to the stock movement report. | V8-010 | In Scope |
| Stock-in page explains actual/landed cost but does not show supplier/product cost references inline. | Managers may confuse product reference cost, supplier reference cost, and actual batch cost. | V8-004 | In Scope |
| Barcode/QR and label print shortcuts exist after stock-in and on active batch detail, but code workflow guidance is minimal. | Staff may choose the wrong label path. | V8-005, V8-007 | In Scope |
| Physical label/printer behavior is not verifiable from automated tests. | Print output can still differ by device and label stock. | V8-007, V8-011 | Needs Verification |

## Non-Gaps

| Area | Decision | Status |
| --- | --- | --- |
| Stock math | No stock math change is required by the audit. | Current |
| Database schema | No migration is required for V8-001. | Current |
| Permissions | Inventory pages remain capability-gated. | Current |
| Auth/OIDC | No change belongs in V8. | Out of Scope |

## Follow-up Actions

- Complete V8-002 to improve batch list/detail visibility without changing stock data.
- Complete V8-003 to make expiry/low-stock next actions clearer.
- Complete V8-004 to verify and polish cost terminology and visibility.
- Complete V8-005 through V8-007 to reduce barcode/QR and label workflow mistakes.
- Complete V8-010 to put movement traceability closer to batch operations.

## Validation

V8-001 is documentation/audit-only. No Django tests were required for this task. Follow-up implementation tasks must include focused tests for any touched view, template, or service behavior.
