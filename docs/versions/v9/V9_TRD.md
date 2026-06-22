# V9 Technical Requirements

Status: Complete
Last updated: 2026-06-16

## Expected Touch Areas

| Module | Scope |
| --- | --- |
| Reports | `reports/views.py`, templates, query filters |
| Audit | `audit/` list filters, display |
| POS | Sale history, reprint audit linkage |
| System | `system_logs/`, health views |

## Constraints

- Report definitions must be owner-approved before calculation changes
- Cancelled sales must not inflate revenue totals
- No change to sale creation/cancellation services unless required and documented
- Export formats (CSV/PDF) need explicit PRD before implementation

## Dependencies

V8 inventory/label clarity helps stock reports.

See `V9_TASKS.md`.
