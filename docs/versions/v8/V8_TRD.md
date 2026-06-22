# V8 Technical Requirements

Status: Complete
Last updated: 2026-06-16

## Expected Touch Areas

| Module | Files |
| --- | --- |
| Inventory | `inventory/views.py`, templates, `inventory/services.py` (careful) |
| Labels | `labels/views.py`, templates |
| POS promotions | `pos/views.py`, `pos/services.py` (display/pricing only) |
| Catalog costs | `catalog/` views for visibility |

## Constraints

- Batch-level stock truth (ADR-0003) must not be bypassed
- Label strategy remains browser-rendered templates (ADR-0005)
- No schema change without explicit approval and migration plan
- Stock services remain transactional

## Dependencies

V7 UX baseline complete or deferred with evidence.

See `V8_TASKS.md`.
