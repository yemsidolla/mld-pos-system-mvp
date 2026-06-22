# V9 Tasks: Reports, Audit, and Owner Control

Status: Complete
Last updated: 2026-06-16

Task statuses start as `Proposed`. When a task is completed, change its status to `Complete` and mark the matching checkbox in `docs/versions/VERSION_COMPLETION_TRACKER.md`. Do not delete completed tasks.

## V9-001

**Task ID:** V9-001  
**Version:** V9  
**Epic:** Owner Control  
**Module:** Dashboard/reports  
**Title:** Owner dashboard/reporting audit  
**Business reason:** Owner needs a clear daily control view.  
**Technical scope:** Audit dashboard home metrics, reports index, report entry points, and owner/manager needs.  
**Files likely affected:** `app/templates/dashboard/home.html`, `app/templates/reports/index.html`, `app/reports/views.py`, docs.  
**Permission impact:** Reports visibility review only.  
**Data impact:** None for audit.  
**UI impact:** Findings may propose report/dashboard UI changes.  
**Docs impact:** Document approved report/control needs.  
**Acceptance criteria:** Owner control gaps are documented and prioritized.  
**Test cases:** None for audit-only.  
**Manual UI check:** Owner/Manager dashboard and reports index.  
**Risk:** Starting implementation before report definitions are approved.  
**Definition of done:** Findings accepted and follow-up tasks tracked.  
**Status:** Complete

## V9-002

**Task ID:** V9-002  
**Version:** V9  
**Epic:** Sales Reporting  
**Module:** Reports  
**Title:** Daily sales report improvement plan  
**Business reason:** Daily sales report is central to owner cash/control review.  
**Technical scope:** Confirm date/time, cancellation, payment method, totals, cost/margin, and empty-state definitions before implementation.  
**Files likely affected:** `app/reports/views.py`, `app/templates/reports/daily_sales.html`, reports tests, docs.  
**Permission impact:** Reports capability unchanged.  
**Data impact:** Report read-only; no sale mutation.  
**UI impact:** Daily report display may change.  
**Docs impact:** Document approved report definition.  
**Acceptance criteria:** Daily sales definition approved; implementation only follows approved definition.  
**Test cases:** Report totals/filter tests if implemented.  
**Manual UI check:** Daily sales report with sales, cancellations, and empty state.  
**Risk:** Incorrect totals can mislead owner.  
**Definition of done:** Definition approved, tests pass if implemented, tracker updated.  
**Status:** Complete

## V9-003

**Task ID:** V9-003  
**Version:** V9  
**Epic:** Staff Accountability  
**Module:** Reports/POS  
**Title:** Staff sales and cashier accountability report  
**Business reason:** Owner should understand staff activity and cashier performance.  
**Technical scope:** Review staff sales report and plan cashier accountability view including sale counts, totals, cancellations, reprints, and overrides if available.  
**Files likely affected:** `app/reports/views.py`, `app/templates/reports/staff_sales.html`, `app/pos/models.py`, reports/POS tests.  
**Permission impact:** Owner/Manager/Viewer report access review.  
**Data impact:** Read-only report unless new tracking fields are separately approved.  
**UI impact:** Staff report display improvements.  
**Docs impact:** Report definition docs.  
**Acceptance criteria:** Staff activity is visible without exposing unrelated admin data.  
**Test cases:** Staff sales report filters/totals/permission tests.  
**Manual UI check:** Staff report with multiple cashiers.  
**Risk:** Staff metrics can be misinterpreted if definitions are unclear.  
**Definition of done:** Definition approved, tests pass if implemented, tracker updated.  
**Status:** Complete

## V9-004

**Task ID:** V9-004  
**Version:** V9  
**Epic:** Inventory Reporting  
**Module:** Reports/inventory  
**Title:** Stock, low-stock, and expiry reporting review  
**Business reason:** Owner needs clear stock risk visibility.  
**Technical scope:** Review stock summary, low stock, expiry, and stock movement reports for definitions, filters, totals, and action links.  
**Files likely affected:** `app/reports/views.py`, `app/templates/reports/stock_summary.html`, `low_stock.html`, `expiry.html`, `stock_movements.html`, tests.  
**Permission impact:** Reports/inventory access unchanged.  
**Data impact:** Read-only.  
**UI impact:** Report readability improvements.  
**Docs impact:** Document report definitions if changed.  
**Acceptance criteria:** Reports clearly show what is included/excluded and what needs action.  
**Test cases:** Stock/expiry/low-stock report tests.  
**Manual UI check:** Reports with normal, low, warning, critical, and expired stock.  
**Risk:** Wrong inclusion rules can cause wrong purchasing/disposal decisions.  
**Definition of done:** Definitions approved, tests pass if implemented, tracker updated.  
**Status:** Complete

## V9-005

**Task ID:** V9-005  
**Version:** V9  
**Epic:** Promotion Reporting  
**Module:** Reports/promotions  
**Title:** Promotion and below-cost reporting plan  
**Business reason:** Owner should see discount impact and risky below-cost activity.  
**Technical scope:** Plan promotion performance, below-cost override, and discount reporting based on current sale item snapshots.  
**Files likely affected:** `app/reports/views.py`, report templates, `app/pos/models.py`, reports/POS tests, docs.  
**Permission impact:** Cost/profit visibility must remain controlled.  
**Data impact:** Read-only unless approved tracking gaps require model changes.  
**UI impact:** Future report display planning.  
**Docs impact:** Report definitions and backlog.  
**Acceptance criteria:** Clear plan exists for promotion/below-cost reporting and required data is known.  
**Test cases:** None for planning-only; implementation requires report/permission tests.  
**Manual UI check:** Review sample sale item promotion data.  
**Risk:** Current data may not support all desired metrics.  
**Definition of done:** Plan accepted or gaps marked Needs Verification.  
**Status:** Complete

## V9-006

**Task ID:** V9-006  
**Version:** V9  
**Epic:** Sales Exceptions  
**Module:** POS/audit/reports  
**Title:** Sale cancellation and receipt reprint tracking  
**Business reason:** Cancellations and reprints are exception events owners should review.  
**Technical scope:** Review existing audit/reprint/cancellation data and plan/report visibility.  
**Files likely affected:** `app/pos/views.py`, `app/pos/models.py`, `app/audit/models.py`, `app/reports/views.py`, templates, tests.  
**Permission impact:** Sales history/audit/report permissions unchanged.  
**Data impact:** Read-only unless new fields are separately approved.  
**UI impact:** Exception visibility/reporting.  
**Docs impact:** Audit/report docs if behavior changes.  
**Acceptance criteria:** Owner can see or has a plan to see cancellations and reprints clearly.  
**Test cases:** Cancellation/reprint audit and report tests if implemented.  
**Manual UI check:** Sale detail/history/audit log.  
**Risk:** Exception reporting can miss events if audit/action definitions are unclear.  
**Definition of done:** Tracking path verified or gaps documented.  
**Status:** Complete

## V9-007

**Task ID:** V9-007  
**Version:** V9  
**Epic:** Audit Review  
**Module:** Audit  
**Title:** Audit log readability and filters  
**Business reason:** Audit logs should help managers understand risky actions.  
**Technical scope:** Improve or plan audit filters/search, action labels, object references, before/after display, and sensitive data redaction.  
**Files likely affected:** `app/audit/views.py`, `app/templates/audit/audit_log_list.html`, `app/audit/templatetags/*`, audit tests.  
**Permission impact:** Audit capability remains required.  
**Data impact:** Read-only.  
**UI impact:** Audit table/filter readability.  
**Docs impact:** Audit docs if behavior changes.  
**Acceptance criteria:** Audit log is easier to filter and understand without exposing secrets.  
**Test cases:** Audit filter/render/permission tests.  
**Manual UI check:** Audit list with stock, sale, login, role, and settings events.  
**Risk:** Audit display can expose sensitive old/new values.  
**Definition of done:** Audit usability improved, tests pass, tracker updated.  
**Status:** Complete

## V9-008

**Task ID:** V9-008  
**Version:** V9  
**Epic:** System Visibility  
**Module:** System logs/health  
**Title:** System logs and health review  
**Business reason:** Owner/operator needs production troubleshooting visibility without exposing secrets.  
**Technical scope:** Review live logs, system health checks, last error, database/log/disk checks, and access restrictions.  
**Files likely affected:** `app/system_logs/views.py`, `app/templates/system_logs/*.html`, `app/core/views.py`, system tests, docs.  
**Permission impact:** System capability remains required.  
**Data impact:** Read-only.  
**UI impact:** System/log readability and warning states.  
**Docs impact:** Deployment/runbook docs if operator behavior changes.  
**Acceptance criteria:** System pages help troubleshoot safely and remain restricted.  
**Test cases:** System page permission/render tests.  
**Manual UI check:** Owner/Manager allowed, Cashier denied.  
**Risk:** Logs can expose credentials or tokens.  
**Definition of done:** System visibility verified, tests pass, tracker updated.  
**Status:** Complete

## V9-009

**Task ID:** V9-009  
**Version:** V9  
**Epic:** Daily Control  
**Module:** Operations/reports  
**Title:** Daily closing control checklist planning  
**Business reason:** Daily closing helps owner control cash, sales, exceptions, and stock risk.  
**Technical scope:** Define operational closing checklist and decide whether it remains docs-only or needs dashboard support.  
**Files likely affected:** Docs first; possible future dashboard/report templates if approved.  
**Permission impact:** Owner/Manager only if implemented in dashboard.  
**Data impact:** None unless a closing record model is separately approved.  
**UI impact:** Future only unless approved.  
**Docs impact:** Closing process doc or backlog entry.  
**Acceptance criteria:** Daily closing steps are documented and implementation need is decided.  
**Test cases:** None for docs-only.  
**Manual UI check:** Review reports needed for closing.  
**Risk:** Turning checklist into accounting workflow without enough requirements.  
**Definition of done:** Closing plan accepted or deferred.  
**Status:** Complete

## V9-010

**Task ID:** V9-010  
**Version:** V9  
**Epic:** Owner Operations  
**Module:** Backup/reset visibility  
**Title:** Backup/reset visibility review  
**Business reason:** Owner should know recovery and reset status without weakening safeguards.  
**Technical scope:** Review backup docs/scripts, reset admin runbook, system health visibility, and whether dashboard should show backup/reset status.  
**Files likely affected:** Docs, scripts only if separately approved, system health templates if approved.  
**Permission impact:** Owner/system capability only if dashboard visibility is implemented.  
**Data impact:** No data reset behavior changes.  
**UI impact:** Possible future status display only.  
**Docs impact:** Backup/reset docs and tracker.  
**Acceptance criteria:** Backup/reset visibility gaps are known and safeguards remain strong.  
**Test cases:** None for review-only; script changes require operator tests.  
**Manual UI check:** System health and reset runbook.  
**Risk:** Making reset too visible can invite unsafe use.  
**Definition of done:** Review accepted, no safety weakened, tracker updated.  
**Status:** Complete

## V9-011

**Task ID:** V9-011  
**Version:** V9  
**Epic:** Release  
**Module:** QA/release  
**Title:** V9 QA and release preparation  
**Business reason:** Reports and audit improvements must be trusted before owner uses them for control.  
**Technical scope:** Run V9 QA checklist, confirm report definitions, finalize release note, update tracker/development log.  
**Files likely affected:** `docs/versions/v9/*`, `docs/versions/VERSION_COMPLETION_TRACKER.md`, `docs/DEVELOPMENT_LOG.md`.  
**Permission impact:** Verify only.  
**Data impact:** Verify only.  
**UI impact:** Verify only.  
**Docs impact:** Finalize V9 docs.  
**Acceptance criteria:** Approved tasks complete/deferred with evidence and owner-reviewed definitions.  
**Test cases:** Reports/audit/permission tests based on scope.  
**Manual UI check:** Owner reporting and audit review pass.  
**Risk:** Owner control pages can create false confidence if definitions are unclear.  
**Definition of done:** V9 release note finalized and tracker marked complete.  
**Status:** Complete
