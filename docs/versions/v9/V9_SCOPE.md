# V9 Scope: Reports, Audit, and Owner Control

Status: Complete
Last updated: 2026-06-16

## 1. Version Name

V9 - Reports, Audit, and Owner Control

## 2. Status

Complete. Sidolla approved continuing V7-V10 step by step from the tracked checklist; V9 closed with QA evidence in `docs/versions/v9/V9_QA_CHECKLIST.md`.

## 3. Goal

Improve owner-level visibility, reports, audit review, daily control, and operational accountability.

## 4. Business Reason

A POS system is not only for selling. It must help the owner understand cash, staff activity, stock, promotions, exceptions, and operational risk.

## 5. Current Source Assumptions

| Source | Assumption | Status |
| --- | --- | --- |
| `reports` app | Daily sales, stock summary, low stock, expiry, movement, and staff sales reports exist. | Current |
| `audit.AuditLog` | Audit log records critical actions. | Current |
| `pos.Sale` and `SaleItem` | Sales, cancellations, reprints, and payment data exist. | Current |
| `inventory.InventoryMovement` | Stock changes can be reported from movement rows. | Current |
| Business report definitions | V9 operational definitions are documented; they are not accounting/tax/payroll definitions. | Current |

## 6. In Scope

- Daily owner dashboard/reporting audit.
- Daily sales report improvement.
- Staff sales and cashier accountability report planning.
- Stock, low-stock, and expiry reporting review.
- Promotion performance and below-cost reporting plan.
- Sale cancellation and receipt reprint tracking.
- Audit log readability and filters.
- System logs and health review.
- Daily closing control checklist planning.
- Backup/reset visibility review.

## 7. Out Of Scope

- Full accounting system.
- Tax filing/reporting system.
- Payroll system.
- External BI warehouse.
- Advanced fraud engine or anomaly detection.
- Multi-store consolidated reporting.
- Sale creation logic changes unless required by a documented report bug.

## 8. Dependencies

- Stable V7 UI polish.
- Stable V8 inventory/promotion/label workflows.
- Current reports, audit, sale, sale item, inventory movement, and permission systems.

## 9. Risks

| Risk | Mitigation |
| --- | --- |
| Report totals do not match business expectations. | Confirm definitions with owner before implementation. |
| Audit improvements expose sensitive data. | Keep audit pages capability-gated and redact secrets. |
| Closing checklist becomes unofficial accounting. | Clearly define operational vs accounting use. |
| Report changes accidentally alter sale behavior. | Do not change sale creation unless a documented report bug requires it. |

## 10. Success Criteria

- Owner can review daily sales and staff activity clearly.
- Important exceptions are visible.
- Audit log is easier to search and understand.
- Reports match documented business rules.
- Risky actions remain traceable.
- Daily closing becomes easier to control.

## 11. Task Groups

- V9-001 Owner dashboard/reporting audit.
- V9-002 Daily sales report improvement plan.
- V9-003 Staff sales and cashier accountability report.
- V9-004 Stock, low-stock, and expiry reporting review.
- V9-005 Promotion and below-cost reporting plan.
- V9-006 Sale cancellation and receipt reprint tracking.
- V9-007 Audit log readability and filters.
- V9-008 System logs and health review.
- V9-009 Daily closing control checklist planning.
- V9-010 Backup/reset visibility review.
- V9-011 V9 QA and release preparation.

## 12. Testing Focus

- Report totals, filters, empty states, and permissions.
- Audit search/filter readability and access control.
- Sale cancellation/reprint audit/report behavior.
- System log/health page access and redaction.
- Manual owner review of report definitions.

## 13. Release Criteria

- Owner-approved report definitions for changed reports.
- Approved V9 tasks complete/deferred.
- Report/audit tests pass for touched areas.
- QA checklist and release note finalized.

## 14. Handoff Notes

V9 should begin with report definition confirmation. Avoid implementing “nice” charts or exports before the business meaning of each report is approved.

V9 closed without database migrations. All new owner-control features are read-only and preserve existing permission and cost-visibility rules. Future accounting, tax, payroll, export, or BI work needs a separate tracked version/task.
