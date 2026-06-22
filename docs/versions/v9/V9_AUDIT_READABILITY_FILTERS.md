# V9-007 Audit Log Readability And Filters

Status: Complete
Last updated: 2026-06-16

## Purpose

Make audit logs easier to search and review while preserving read-only, append-only audit behavior.

## Definitions

| Signal | Definition | Status |
| --- | --- | --- |
| Search | Matches action, module, object type, object id, object display, IP, or username. | Current |
| Object type filter | Filters audit rows by stored `object_type`. | Current |
| Risk event | Audit action that usually needs owner/manager review, such as sale cancel, below-cost sale, override, stock adjustment, cost change, role/settings change, data reset, or permission denied. | Current |

## Implementation

- Updated `app/audit/forms.py`.
- Updated `app/audit/views.py`.
- Updated `app/templates/audit/audit_log_list.html`.
- Updated `app/audit/tests.py`.

## What Changed

- Added broad search to the audit filter form.
- Added object-type filter.
- Added Entries, Risk Events, Modules, Users, Mode, and Order summary cards.
- Added risk review badge and object type/id metadata in the table.

## What Did Not Change

- No audit model changes.
- No audit writer/service changes.
- No create/update/delete path was added.
- No database migrations were introduced.

## Verification

```bash
docker compose run --rm --no-deps -v "$PWD/app:/app" web python manage.py test audit.tests.AuditLogDashboardTests --noinput --verbosity 1
```

Result: 5 tests OK.
