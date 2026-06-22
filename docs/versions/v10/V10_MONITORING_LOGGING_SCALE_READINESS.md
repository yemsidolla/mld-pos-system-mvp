# V10-008 Monitoring / Logging Scale-readiness Review

Status: Complete
Last updated: 2026-06-16

## Purpose

Review current observability and define future scale-readiness gaps without changing logging behavior.

## Current Observability

| Capability | Evidence | Status |
| --- | --- | --- |
| App/error log files | Django logging writes to log files configured in settings. | Current |
| Live logs page | `app/system_logs/views.py::live_logs_view` with redaction helpers and admin/system access. | Current |
| System health page | Checks database, disk, log writeability, last sale, last stock-in, and last error. | Current |
| Health endpoint | `/health/` exists for simple liveness. | Current |
| Audit logs | Business/security actions use `AuditLog`. | Current |
| Backup/reset visibility | System Health links runbooks and commands after V9. | Current |

## Scale Gaps

| Gap | Status | Recommendation |
| --- | --- | --- |
| Log rotation policy is not visible in app docs. | Needs Verification | Add VPS logrotate or Docker logging runbook. |
| Alerting is not configured from repository docs. | Missing | Future ops task for uptime, disk, DB, and error alerts. |
| Centralized logs are not configured. | Future / Proposed | Consider only if production troubleshooting needs it. |
| Health page does not expose performance metrics. | Future / Proposed | Add cautiously; avoid leaking sensitive environment details. |
| Last error display depends on log file content. | Current | Preserve redaction and keep system-only access. |

## Safety Rules

| Rule | Status |
| --- | --- |
| Do not expose secrets, passwords, session tokens, OIDC secrets, MinIO keys, or full environment values in logs. | Current |
| Live logs and system health stay behind system capability checks. | Current |
| Operational logs are for troubleshooting, not business audit replacement. | Current |
| Business-critical actions should continue creating `AuditLog` records. | Current |

## Future Test Requirements

If monitoring/logging code changes later:

- System health remains admin/system-only.
- Redaction removes common secret/token patterns.
- Missing log files render a safe warning, not a server error.
- Health checks do not expose raw environment values.
- Browser mobile/desktop system pages remain readable.

## Verification

Planning/review only. No logging configuration or system page behavior changed.

