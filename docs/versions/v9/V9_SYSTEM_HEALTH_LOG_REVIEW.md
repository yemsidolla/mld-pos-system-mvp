# V9-008 System Logs And Health Review

Status: Complete
Last updated: 2026-06-16

## Purpose

Improve safe operator visibility for production troubleshooting without exposing secrets.

## Definitions

| Signal | Definition | Status |
| --- | --- | --- |
| Overall health | `OK`, `Review`, or `Attention` based on database, log writable, disk status, and latest error presence. | Current |
| Disk used percent | Human-readable disk usage percentage from the active data/log/media/static path. | Current |
| Log line counts | Count of sanitized app/error log lines currently displayed. | Current |
| Log redaction | Sensitive settings/environment values are replaced with `[REDACTED]`. | Current |

## Implementation

- Updated `app/system_logs/views.py`.
- Updated `app/templates/system_logs/system_health.html`.
- Updated `app/templates/system_logs/live_logs.html`.
- Updated `app/system_logs/tests.py`.

## What Changed

- Added overall system status to System Health.
- Added disk used percent and disk status.
- Added operator notes that point staff toward Live Logs and deployment runbooks.
- Added app/error line count cards to Live Logs.

## What Did Not Change

- No log file paths or logging configuration changed.
- No log redaction behavior was weakened.
- No access permissions changed.
- No database migrations were introduced.

## Verification

```bash
docker compose run --rm --no-deps -v "$PWD/app:/app" web python manage.py test system_logs.tests.SystemLogTests --noinput --verbosity 1
```

Result: 6 tests OK.
