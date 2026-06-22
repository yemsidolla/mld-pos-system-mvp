# V9-001 Owner Dashboard And Reporting Audit

Status: Complete
Last updated: 2026-06-16

## Purpose

Review the current owner-facing dashboard, report entry points, and available data before implementing V9 reporting and control polish.

## Source Review

| Area | Evidence | Status |
| --- | --- | --- |
| Dashboard home | `app/core/views.py::dashboard_home_view`, `app/templates/dashboard/home.html` | Current |
| Reports index | `app/reports/views.py::reports_index_view`, `app/templates/reports/index.html` | Current |
| Daily sales | `app/reports/views.py::daily_sales_report_view`, `app/templates/reports/daily_sales.html` | Mostly Current |
| Staff sales | `app/reports/views.py::staff_sales_report_view`, `app/templates/reports/staff_sales.html` | Mostly Current |
| Stock risk reports | `stock_summary_report_view`, `low_stock_report_view`, `expiry_report_view` | Mostly Current |
| Movement traceability | `stock_movement_report_view` | Current after V8 |
| Sales exceptions | `pos.Sale.status`, `Sale.cancel_reason`, `AuditLog.Action.SALE_CANCEL`, `AuditLog.Action.RECEIPT_PRINT` | Current |
| Promotion impact data | `SaleItem` promotion, discount, cost, override snapshot fields | Current |
| Audit review | `audit_log_list_view`, `AuditLogFilterForm`, `audit_extras.change_rows` | Mostly Current |
| System health/logs | `system_health_view`, `live_logs_view`, log redaction helpers | Mostly Current |

## What Works Today

| Capability | Status | Notes |
| --- | --- | --- |
| Owner/manager dashboard entry point | Current | Dashboard shows sales count, active products, active batches, low stock, expiring batches, recent sales, and recent upload jobs when the user has matching capabilities. |
| Report launcher | Current | Reports index links to daily sales, stock summary, low stock, expiry, stock movement, and staff sales reports. |
| Daily sales total | Mostly Current | Completed sale count and revenue are separated from the full sale list, but report definition text does not yet make cancelled-sale inclusion/exclusion clear enough. |
| Stock risk visibility | Mostly Current | V8 added reorder gaps, expiry days, and actions. V9 can make report definition and owner handoff clearer. |
| Staff sales | Mostly Current | Completed sale count and total by cashier exist, but accountability signals such as cancellations, reprints, overrides, and average sale are not yet visible together. |
| Exception audit data | Current | Cancellation and receipt reprint audit events exist. They are not summarized in reports yet. |
| Promotion safety data | Current | Sale items keep promotion name, discount, cost basis, below-cost override user, and override reason snapshots. |
| Audit filters | Mostly Current | Action, module, user, and date filters exist. Search/object filtering and risk summaries can be improved without changing audit records. |
| System visibility | Mostly Current | Database, log writable, disk, last sale, last stock-in, and last error are visible. Backup/reset visibility is docs/script-driven, not dashboard-driven. |

## Gaps And Follow-Up Tasks

| Gap | Status | Follow-up |
| --- | --- | --- |
| Reports index is a launcher, not an owner control hub. | Missing | V9-002 through V9-004 should add clearer report definitions and summary cards where data already exists. |
| Daily sales page does not show completed/cancelled split, payment totals, discounts, or cost/margin where allowed. | Missing | V9-002 |
| Staff sales report does not show cancellation, reprint, below-cost override, or average-sale accountability signals. | Missing | V9-003 |
| Stock reports need clearer owner-level definition text and risk prioritization. | Mostly Current | V9-004 |
| Promotion and below-cost reporting is not surfaced as a dedicated owner view. | Missing | V9-005 |
| Cancellation and receipt reprint exceptions are visible only by drilling into sales/audit. | Missing | V9-006 |
| Audit list needs better search/object filters and risk-focused summary. | Mostly Current | V9-007 |
| System health does not summarize backup/reset operator posture. | Needs Verification | V9-008 and V9-010 |
| Daily closing process is not documented as an operational checklist. | Missing | V9-009 |

## Approved V9 Implementation Direction

| Decision | Status |
| --- | --- |
| Keep all V9 report changes read-only unless a documented bug requires service changes. | Current |
| Do not add CSV/PDF exports in V9 without a separate PRD. | Current |
| Do not add accounting, payroll, BI, fraud detection, or multi-store reporting in V9. | Current |
| Use current Django templates, report views, and dashboard design system. | Current |
| Preserve existing permission gates for reports, audit, sales history, system health, and cost visibility. | Current |

## Definition Notes

- Daily sales revenue means completed sales only.
- Cancelled sales should be counted as exceptions, not revenue.
- Cost and margin must be visible only when the current user can view costs.
- Receipt reprint tracking is currently audit-backed, not a counter field on `Sale`.
- Promotion reporting can use sale-item snapshots. It should not recalculate old prices from current promotion rules.

## Verification

This was a source/documentation audit only. No Django tests were required for V9-001 because no application behavior changed.
