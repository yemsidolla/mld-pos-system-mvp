# Version Completion Tracker

Status: Current
Last updated: 2026-06-16

This is the durable checklist for V7-V10. When work is finished, mark the checkbox and change the task status in the matching `V*_TASKS.md` file. Do not delete completed tasks; the completed row is the evidence that the work already happened.

## Tracking Rules

| Rule | Status |
| --- | --- |
| Keep completed items in place. | Current |
| Mark finished work as `Complete`, not deleted. | Current |
| Add completion evidence such as commit, PR, release note, test result, or reviewer note. | Current |
| If a task is intentionally not implemented, mark it `Deferred` or `Superseded` and explain why. | Current |
| Sidolla approved continuing V7-V10 step by step after planning on 2026-06-16; future scope changes still need a tracked task. | Current |
| If implementation changes scope, update the relevant version scope doc before coding. | Current |

## Status Legend

| Status | Meaning |
| --- | --- |
| Proposed | Planned but not approved for implementation. |
| Approved | Sidolla approved the task/version to begin. |
| In Progress | Work has started. |
| Human Reviewing | Ready for review/testing by Sidolla or assigned reviewer. |
| Complete | Finished, tested as required, documented, and accepted. |
| Deferred | Valid task but intentionally moved later. |
| Superseded | Replaced by another task/decision; keep the row for history. |
| Blocked | Cannot continue without a decision, access, data, or external dependency. |

## Version Completion

| Done | Version | Scope Doc | Task Doc | Status | Completion Evidence |
| --- | --- | --- | --- | --- | --- |
| [x] | V7 UX/UI Cleanup & Staff Workflow Polish | `docs/versions/v7/V7_SCOPE.md` | `docs/versions/v7/V7_TASKS.md` | Complete | V7-001 through V7-012 complete; final QA checklist and release note complete; 142 mounted-source V7 regression tests OK; phone/tablet/desktop and Khmer browser checks recorded. |
| [x] | V8 Inventory, Label, and Promotion Professionalization | `docs/versions/v8/V8_SCOPE.md` | `docs/versions/v8/V8_TASKS.md` | Complete | V8-001 through V8-011 complete; final QA checklist and release note complete; mounted-source check, collectstatic, full 311-test suite, and desktop/phone browser smoke checks passed. |
| [x] | V9 Reports, Audit, and Owner Control | `docs/versions/v9/V9_SCOPE.md` | `docs/versions/v9/V9_TASKS.md` | Complete | V9-001 through V9-011 complete; final QA checklist and release note complete; mounted-source check, collectstatic, full 319-test suite, and desktop/phone browser smoke checks passed. |
| [x] | V10 Multi-store / Scale-readiness Foundation | `docs/versions/v10/V10_SCOPE.md` | `docs/versions/v10/V10_TASKS.md` | Complete | V10-001 through V10-011 complete as planning/scale-readiness deliverables; ADR-0008 created; no multi-store schema, permission, route, template, or service behavior implemented. |

## V7 Checklist

| Done | Task | Status | Completion Evidence |
| --- | --- | --- | --- |
| [x] | V7-001 Navigation and naming cleanup audit | Complete | Renamed Store Settings, Login & Authentication, and Style Guide labels; `manage.py check` clean; 13 targeted tests OK. |
| [x] | V7-002 Dashboard home polish | Complete | Added role-safe Print Labels and Batch Upload shortcuts; standardized Open POS wording; `manage.py check` clean; 8 focused tests OK. |
| [x] | V7-003 POS cashier workflow polish | Complete | Fixed quick keys to submit original barcodes and hide no-barcode products; `manage.py check` clean; 22 targeted tests and 41 POS tests OK. |
| [x] | V7-004 Catalog/product list polish | Complete | Added visible search row, scan/search controls, table scroll wrapper, stronger empty state, and image-render test; mounted-source check clean; 19 catalog tests and 55 V7 regression tests OK. |
| [x] | V7-005 Inventory and stock receiving workflow polish | Complete | Added stock-in help text, receive-another shortcut, inventory low-stock level, batch open action, and batch action guidance/errors; mounted-source check clean; 23 inventory tests and 78 V7 regression tests OK. |
| [x] | V7-006 Promotion and label page polish | Complete | Added promotion label links, timeline status, form help, Print Labels scan lookup, and label print help text; mounted-source check clean; 18 focused tests and 93 V7 regression tests OK. |
| [x] | V7-007 Reports page readability polish | Complete | Added report metric summaries, lateral links, table scroll wrappers, stock level badges, expiry severity badges/links, and low-stock stock actions; mounted-source check clean; 11 reports tests and 104 V7 regression tests OK. |
| [x] | V7-008 Audit/log/system pages polish | Complete | Added audit read-only metrics, human-readable system health cards/details, live-log safety guidance, and clearer log panels; mounted-source check clean; 15 audit/system tests and 119 V7 regression tests OK. |
| [x] | V7-009 Empty/error/access-denied states polish | Complete | Added status-specific error guidance, safer error footer notes, and stronger empty states for batch uploads, sales history, users, and label templates; mounted-source check clean; 16 focused tests and 139 V7 regression tests OK. |
| [x] | V7-010 Mobile/tablet usability pass | Complete | Added responsive topbar/table/scanner/payment/auth/mobile-nav guards; browser-checked phone/tablet/desktop layouts; mounted-source check clean; 36 focused tests and 140 V7 regression tests OK; collectstatic completed. |
| [x] | V7-011 English/Khmer wording consistency review | Complete | Wrapped V7 Python copy in gettext, added/compiled focused Khmer translations, browser-checked Khmer product/inventory/error pages; mounted-source check clean; 29 focused tests and 142 V7 regression tests OK. |
| [x] | V7-012 V7 QA and release preparation | Complete | Finalized V7 QA checklist and release note; closed V7 scope/tasks/tracker; recorded final regression, browser, and rollback evidence. |

## V8 Checklist

| Done | Task | Status | Completion Evidence |
| --- | --- | --- | --- |
| [x] | V8-001 Inventory workflow audit | Complete | Created `docs/versions/v8/V8_INVENTORY_WORKFLOW_AUDIT.md`; confirmed stock services are transaction-safe and tracked operational visibility follow-ups into V8-002 through V8-010. |
| [x] | V8-002 Stock batch list/detail improvement plan | Complete | Added richer batch list/detail context, cost-safe display, generated-code status, and focused inventory tests; see `docs/versions/v8/V8_STOCK_BATCH_VISIBILITY_POLISH.md`. |
| [x] | V8-003 Expiry and low-stock operational flow | Complete | Added reorder gap, stock-state actions, expiry days, supplier context, and focused inventory/report tests; see `docs/versions/v8/V8_EXPIRY_LOW_STOCK_FLOW_POLISH.md`. |
| [x] | V8-004 Supplier/product cost visibility review | Complete | Stock-in is now cost-visibility gated; reference/default/actual/landed cost wording is clearer; focused cost/catalog/inventory tests passed. |
| [x] | V8-005 Barcode/QR workflow polish | Complete | Added code workflow guidance, selected-batch print checks, scanner quality hint, and focused barcode/scanner tests. |
| [x] | V8-006 Label template management polish | Complete | Added template metrics, field summaries, grouped form sections, help text, guide update, and label tests. |
| [x] | V8-007 Product/shelf/promotion label workflow | Complete | Added product/shelf and promotion print summaries, clearer setup warnings, guide update, and label tests. |
| [x] | V8-008 Promotion setup and lifecycle polish | Complete | Added lifecycle metrics/details, grouped form sections, product-or-category scope validation, docs, and promotion tests. |
| [x] | V8-009 POS promotion visibility and below-cost review | Complete | Added POS promotion savings, below-cost manager/admin warnings, and focused POS pricing/page tests. |
| [x] | V8-010 Inventory audit and movement traceability review | Complete | Added movement report filters, gated batch/audit links, batch movement preview evidence, and report/audit tests. |
| [x] | V8-011 V8 QA and release preparation | Complete | Finalized V8 QA checklist, release note, scope, tasks, tracker, and development log; mounted-source check, collectstatic, full 311-test suite, and desktop/phone browser smoke checks passed. |

## V9 Checklist

| Done | Task | Status | Completion Evidence |
| --- | --- | --- | --- |
| [x] | V9-001 Owner dashboard/reporting audit | Complete | Created `docs/versions/v9/V9_OWNER_CONTROL_AUDIT.md`; mapped current owner controls, missing report gaps, and follow-up tasks. |
| [x] | V9-002 Daily sales report improvement plan | Complete | Added daily report definition, completed/cancelled split, gross/discount/net/average metrics, payment breakdown, cost/margin visibility guard, linked sale details, and report tests. |
| [x] | V9-003 Staff sales and cashier accountability report | Complete | Added cashier accountability signals for completed sales, cancellations, receipt reprints, below-cost overrides, discounts, average sale, and cost/margin visibility; report tests passed. |
| [x] | V9-004 Stock, low-stock, and expiry reporting review | Complete | Added stock/low-stock/expiry report definitions, out-of-stock/healthy/review-now metrics, low-stock urgency ordering, and report tests. |
| [x] | V9-005 Promotion and below-cost reporting plan | Complete | Added Promotion & Below-cost Report route/page/menu link using completed sale-item snapshots, below-cost review, cost/margin visibility guard, and report tests. |
| [x] | V9-006 Sale cancellation and receipt reprint tracking | Complete | Added sales-history status filter and exception summary, sale-detail reprint count and audit-backed exception table, plus POS cancellation/reprint tests. |
| [x] | V9-007 Audit log readability and filters | Complete | Added audit search, object-type filter, risk-event summary, object metadata, risk badges, and audit dashboard tests. |
| [x] | V9-008 System logs and health review | Complete | Added overall system status, disk percent/status, Live Logs line counts, operator notes, and system log tests while preserving redaction/access rules. |
| [x] | V9-009 Daily closing control checklist planning | Complete | Added read-only Daily Closing Checklist page, report evidence links, shared checklist styling, and report tests; no closing model/accounting workflow added. |
| [x] | V9-010 Backup/reset visibility review | Complete | Added System Health backup/reset safeguards panel with backup commands, runbook paths, and explicit no-dashboard-reset safety copy; system tests passed. |
| [x] | V9-011 V9 QA and release preparation | Complete | Finalized V9 QA checklist, release note, scope, tasks, tracker, and development log; mounted-source check, collectstatic, full 319-test suite, and desktop/phone browser smoke checks passed. |

## V10 Checklist

| Done | Task | Status | Completion Evidence |
| --- | --- | --- | --- |
| [x] | V10-001 Multi-store readiness audit | Complete | Created `docs/versions/v10/V10_MULTI_STORE_READINESS_AUDIT.md`; mapped single-store assumptions, risks, and follow-up planning. |
| [x] | V10-002 Store/location model planning | Complete | Created `docs/versions/v10/V10_STORE_LOCATION_MODEL_PLAN.md`; proposed future `Store` direction and migration sequence without adding schema. |
| [x] | V10-003 Store-level permission planning | Complete | Created `docs/versions/v10/V10_STORE_LEVEL_PERMISSION_PLAN.md`; documented future user/store access model and tests without changing current permissions. |
| [x] | V10-004 Store-level inventory planning | Complete | Created `docs/versions/v10/V10_STORE_LEVEL_INVENTORY_PLAN.md`; preserved batch-level inventory rule and documented future store-scoped stock rules. |
| [x] | V10-005 Store-level reporting planning | Complete | Created `docs/versions/v10/V10_STORE_LEVEL_REPORTING_PLAN.md`; documented report/store filter dependencies and future tests. |
| [x] | V10-006 Store settings separation review | Complete | Created `docs/versions/v10/V10_STORE_SETTINGS_SEPARATION_REVIEW.md`; mapped singleton settings and future per-store split risks. |
| [x] | V10-007 Deployment and backup hardening review | Complete | Created `docs/versions/v10/V10_DEPLOYMENT_BACKUP_HARDENING_REVIEW.md`; reviewed compose, host Nginx, backup/restore scripts, and restore rehearsal gaps. |
| [x] | V10-008 Monitoring/logging scale-readiness review | Complete | Created `docs/versions/v10/V10_MONITORING_LOGGING_SCALE_READINESS.md`; documented logging, health, redaction, and future alerting gaps. |
| [x] | V10-009 Data retention and audit retention plan | Complete | Created `docs/versions/v10/V10_DATA_RETENTION_AUDIT_RETENTION_PLAN.md`; documented retention principles and confirmed no deletion/archival behavior added. |
| [x] | V10-010 Performance and database review | Complete | Created `docs/versions/v10/V10_PERFORMANCE_DATABASE_REVIEW.md`; reviewed pagination, indexes, query patterns, and future optimization candidates. |
| [x] | V10-011 V10 QA and release preparation | Complete | Finalized V10 QA checklist, release note, scope, tasks, tracker, and ADR-0008; validation was documentation-only because V10 made no app changes. |
