# V10 Tasks: Multi-store / Scale-readiness Foundation

Status: Complete
Last updated: 2026-06-16

Task statuses start as `Proposed`. When a task is completed, change its status to `Complete` and mark the matching checkbox in `docs/versions/VERSION_COMPLETION_TRACKER.md`. Do not delete completed tasks.

V10 is complete as a planning/scale-readiness package only. No multi-store implementation, schema change, permission behavior change, route, template, or service mutation was added by V10.

## V10-001

**Task ID:** V10-001  
**Version:** V10  
**Epic:** Scale Readiness  
**Module:** Product/architecture  
**Title:** Multi-store readiness audit  
**Business reason:** Melodu needs to understand future multi-store risk before changing the data model.  
**Technical scope:** Audit current models, routes, permissions, reports, settings, and workflows for single-store assumptions.  
**Files likely affected:** Docs first; source inspection across apps; no implementation unless separately approved.  
**Permission impact:** Review only.  
**Data impact:** Review only.  
**UI impact:** Review only.  
**Docs impact:** Record assumptions, risks, and future decisions.  
**Acceptance criteria:** Single-store assumptions are documented with risk level and recommended next steps.  
**Test cases:** None for audit-only.  
**Manual UI check:** Review current workflows for store assumptions.  
**Risk:** Missing hidden assumptions can make later migrations expensive.  
**Definition of done:** Audit accepted, risks tracked, tracker updated.  
**Status:** Complete  
**Completion evidence:** `docs/versions/v10/V10_MULTI_STORE_READINESS_AUDIT.md`

## V10-002

**Task ID:** V10-002  
**Version:** V10  
**Epic:** Data Model Planning  
**Module:** Store/location model  
**Title:** Store/location model planning  
**Business reason:** A store/location concept is the foundation of future multi-store behavior.  
**Technical scope:** Plan whether store/location belongs on users, stock batches, sales, settings, reports, labels, and audit records.  
**Files likely affected:** Docs and ADR first; possible future `core`/`inventory`/`pos`/`reports` models if approved later.  
**Permission impact:** Future store-level access implications.  
**Data impact:** High if later implemented; planning only now.  
**UI impact:** Future store selector/filters may be needed.  
**Docs impact:** ADR/backlog update if a direction is chosen.  
**Acceptance criteria:** Proposed data model direction and migration risks are documented.  
**Test cases:** None for planning-only.  
**Manual UI check:** Not applicable beyond workflow review.  
**Risk:** Premature schema changes can damage production data.  
**Definition of done:** Plan reviewed and marked Proposed/Approved/Deferred.  
**Status:** Complete  
**Completion evidence:** `docs/versions/v10/V10_STORE_LOCATION_MODEL_PLAN.md`

## V10-003

**Task ID:** V10-003  
**Version:** V10  
**Epic:** Authorization Planning  
**Module:** Permissions/accounts  
**Title:** Store-level permission planning  
**Business reason:** Future multi-store users may need access to one or more locations.  
**Technical scope:** Plan user/store assignment, role capability scoping, owner/manager hierarchy, and cashier restrictions.  
**Files likely affected:** Docs first; possible future `accounts`, `core.permissions`, `core.capabilities`, tests.  
**Permission impact:** High if implemented later.  
**Data impact:** Possible future user/store relationship.  
**UI impact:** Possible future user management changes.  
**Docs impact:** Permission matrix and ADR if direction approved.  
**Acceptance criteria:** Store-level permission model options and risks are documented.  
**Test cases:** None for planning-only; implementation needs permission tests.  
**Manual UI check:** User/role screens review.  
**Risk:** Wrong permission model can expose store data.  
**Definition of done:** Permission plan accepted or deferred.  
**Status:** Complete  
**Completion evidence:** `docs/versions/v10/V10_STORE_LEVEL_PERMISSION_PLAN.md`

## V10-004

**Task ID:** V10-004  
**Version:** V10  
**Epic:** Inventory Planning  
**Module:** Inventory  
**Title:** Store-level inventory planning  
**Business reason:** Stock quantities must be location-aware before true multi-store use.  
**Technical scope:** Plan whether store belongs on stock batches, movements, stock-in, adjustments, transfers, labels, and reports.  
**Files likely affected:** Docs first; possible future `inventory` models/services/views/tests.  
**Permission impact:** Future store-scoped inventory access.  
**Data impact:** High if implemented later.  
**UI impact:** Future store filters/selectors.  
**Docs impact:** Inventory roadmap/backlog.  
**Acceptance criteria:** Store-level inventory direction and transfer out-of-scope boundaries are clear.  
**Test cases:** None for planning-only.  
**Manual UI check:** Review stock-in, stock overview, batch detail.  
**Risk:** Multi-store inventory is easy to get wrong without clear transfer rules.  
**Definition of done:** Plan accepted or deferred.  
**Status:** Complete  
**Completion evidence:** `docs/versions/v10/V10_STORE_LEVEL_INVENTORY_PLAN.md`

## V10-005

**Task ID:** V10-005  
**Version:** V10  
**Epic:** Reporting Planning  
**Module:** Reports  
**Title:** Store-level reporting planning  
**Business reason:** Future owners may need per-store and combined reporting.  
**Technical scope:** Plan store filters/grouping for daily sales, staff sales, stock, expiry, movements, audit, and closing.  
**Files likely affected:** Docs first; possible future `reports` views/templates/tests.  
**Permission impact:** Store-scoped report visibility.  
**Data impact:** Read-only planning; future schema dependency.  
**UI impact:** Future report filter design.  
**Docs impact:** Report roadmap/backlog.  
**Acceptance criteria:** Reporting needs and data dependencies are documented.  
**Test cases:** None for planning-only.  
**Manual UI check:** Review current reports.  
**Risk:** Report plan depends on store data model decisions.  
**Definition of done:** Plan accepted or deferred.  
**Status:** Complete  
**Completion evidence:** `docs/versions/v10/V10_STORE_LEVEL_REPORTING_PLAN.md`

## V10-006

**Task ID:** V10-006  
**Version:** V10  
**Epic:** Settings Planning  
**Module:** Store settings  
**Title:** Store settings separation review  
**Business reason:** Receipts, logos, KHQR, costs, labels, and settings may differ by location.  
**Technical scope:** Review current `StoreSetting` singleton and plan future per-store settings boundaries.  
**Files likely affected:** Docs first; possible future `core.models`, settings views/forms/templates/tests.  
**Permission impact:** Future store settings permissions.  
**Data impact:** High if singleton becomes per-store later.  
**UI impact:** Future settings selection/navigation.  
**Docs impact:** ADR/backlog if direction chosen.  
**Acceptance criteria:** Singleton limitations and migration options are documented.  
**Test cases:** None for planning-only.  
**Manual UI check:** Store settings page.  
**Risk:** Settings migration can affect receipts, labels, and payments.  
**Definition of done:** Settings separation plan accepted or deferred.  
**Status:** Complete  
**Completion evidence:** `docs/versions/v10/V10_STORE_SETTINGS_SEPARATION_REVIEW.md`

## V10-007

**Task ID:** V10-007  
**Version:** V10  
**Epic:** Operations Hardening  
**Module:** Deployment/backup  
**Title:** Deployment and backup hardening review  
**Business reason:** Scale requires recovery confidence and clear production procedures.  
**Technical scope:** Review compose files, host Nginx assumptions, database/media/MinIO backup/restore scripts, deployment runbooks, and restore rehearsal needs.  
**Files likely affected:** Docs/scripts only if separately approved.  
**Permission impact:** None.  
**Data impact:** Backup/restore safety review.  
**UI impact:** None unless system health visibility is approved.  
**Docs impact:** Deployment/backup/runbook updates.  
**Acceptance criteria:** Deployment and recovery gaps are documented with next actions.  
**Test cases:** Non-production backup/restore rehearsal if scripts change.  
**Manual UI check:** Health/static/media after deploy if implementation occurs.  
**Risk:** Poor recovery planning can cause downtime/data loss.  
**Definition of done:** Hardening review accepted, tracker updated.  
**Status:** Complete  
**Completion evidence:** `docs/versions/v10/V10_DEPLOYMENT_BACKUP_HARDENING_REVIEW.md`

## V10-008

**Task ID:** V10-008  
**Version:** V10  
**Epic:** Observability  
**Module:** Monitoring/logging  
**Title:** Monitoring/logging scale-readiness review  
**Business reason:** Larger operations need reliable troubleshooting without secret exposure.  
**Technical scope:** Review logging files, live log viewer, system health checks, last error display, and future monitoring needs.  
**Files likely affected:** Docs first; possible future `system_logs`, `core.views`, logging settings, tests.  
**Permission impact:** System capability remains required.  
**Data impact:** None.  
**UI impact:** Possible future system health/log display improvements.  
**Docs impact:** Ops/runbook updates.  
**Acceptance criteria:** Monitoring/logging gaps and secret-redaction risks are documented.  
**Test cases:** System page tests if implementation occurs.  
**Manual UI check:** Live logs/system health.  
**Risk:** Logs can leak credentials or fail under production load.  
**Definition of done:** Review accepted, tracker updated.  
**Status:** Complete  
**Completion evidence:** `docs/versions/v10/V10_MONITORING_LOGGING_SCALE_READINESS.md`

## V10-009

**Task ID:** V10-009  
**Version:** V10  
**Epic:** Data Governance  
**Module:** Audit/data retention  
**Title:** Data retention and audit retention plan  
**Business reason:** Long-term data growth needs clear retention rules without losing auditability.  
**Technical scope:** Plan retention for sales, audit logs, inventory movements, media, logs, backups, and reset-safe data.  
**Files likely affected:** Docs first; future scripts/commands only if approved.  
**Permission impact:** Owner/system capability if retention controls are later exposed.  
**Data impact:** High if deletion/archival is implemented later.  
**UI impact:** Future admin/system visibility only.  
**Docs impact:** Data governance/backup docs.  
**Acceptance criteria:** Retention policy options and risks are documented; no data deletion added.  
**Test cases:** None for planning-only; implementation requires destructive-action tests.  
**Manual UI check:** Not applicable.  
**Risk:** Retention work can accidentally delete business/audit data.  
**Definition of done:** Plan accepted or deferred.  
**Status:** Complete  
**Completion evidence:** `docs/versions/v10/V10_DATA_RETENTION_AUDIT_RETENTION_PLAN.md`

## V10-010

**Task ID:** V10-010  
**Version:** V10  
**Epic:** Performance  
**Module:** Database/application  
**Title:** Performance and database review  
**Business reason:** As data grows, slow POS, reports, or inventory pages can harm operations.  
**Technical scope:** Review query patterns, pagination, indexes, report queries, media load, and page render bottlenecks.  
**Files likely affected:** Docs first; possible future model indexes, query changes, tests.  
**Permission impact:** None unless query scoping changes.  
**Data impact:** Possible future migrations for indexes only if approved.  
**UI impact:** None unless loading/empty states change.  
**Docs impact:** Performance notes/backlog.  
**Acceptance criteria:** Baseline risks and candidate optimizations are documented.  
**Test cases:** None for review-only; implementation requires query/result regression tests.  
**Manual UI check:** Identify slow pages with realistic data if available.  
**Risk:** Premature optimization can change report results or add migration risk.  
**Definition of done:** Review accepted, tracker updated.  
**Status:** Complete  
**Completion evidence:** `docs/versions/v10/V10_PERFORMANCE_DATABASE_REVIEW.md`

## V10-011

**Task ID:** V10-011  
**Version:** V10  
**Epic:** Release  
**Module:** QA/release  
**Title:** V10 QA and release preparation  
**Business reason:** Scale-readiness decisions should be captured safely before the next phase.  
**Technical scope:** Run V10 QA checklist, finalize release notes, update tracker/development log, and create ADRs for approved major decisions.  
**Files likely affected:** `docs/versions/v10/*`, `docs/versions/VERSION_COMPLETION_TRACKER.md`, `docs/decisions/*`, `docs/DEVELOPMENT_LOG.md`.  
**Permission impact:** Verify only unless implementation occurred.  
**Data impact:** Verify only unless implementation occurred.  
**UI impact:** Verify only unless implementation occurred.  
**Docs impact:** Finalize V10 docs and decisions.  
**Acceptance criteria:** Approved tasks complete/deferred with clear future decisions and risk notes.  
**Test cases:** Docs-only validation or targeted tests for any implemented code.  
**Manual UI check:** Only if implementation occurred.  
**Risk:** Future scale work starts without enough decision clarity.  
**Definition of done:** V10 release note finalized and tracker marked complete.  
**Status:** Complete  
**Completion evidence:** `docs/versions/v10/V10_QA_CHECKLIST.md`, `docs/versions/v10/V10_RELEASE_NOTE.md`, `docs/versions/VERSION_COMPLETION_TRACKER.md`
