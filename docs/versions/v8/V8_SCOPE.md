# V8 Scope: Inventory, Label, and Promotion Professionalization

Status: Complete
Last updated: 2026-06-16

## 1. Version Name

V8 - Inventory, Label, and Promotion Professionalization

## 2. Status

Complete. V8 was completed task-by-task from the tracked checklist and closed with QA evidence in `docs/versions/v8/V8_QA_CHECKLIST.md`.

## 3. Goal

Make inventory control, label printing, barcode/QR workflows, and promotion handling more professional and reliable for daily operations.

## 4. Business Reason

Melodu Pet Store depends on accurate stock, clean labels, visible pricing, and practical promotions. V8 should improve operational control without redesigning the whole system.

## 5. Current Source Assumptions

| Source | Assumption | Status |
| --- | --- | --- |
| `inventory.StockBatch` and `InventoryMovement` | Batch-level stock and movement ledger already exist. | Current |
| `inventory.services.receive_stock()` | Stock-in service creates batch, codes, movement, and audit. | Current |
| `labels.LabelTemplate` | Product/promotion/custom label templates exist. | Current |
| `pos.Promotion` | Promotion setup and POS pricing hooks exist. | Current |
| `docs/DESIGN_SYSTEM.md` | UI improvements must reuse current design rules. | Current |
| Physical label/receipt printer behavior | Needs real-device verification. | Needs Verification |

## 6. In Scope

- Inventory receiving workflow review.
- Stock batch visibility improvement.
- Expiry and low-stock workflow improvement.
- Supplier/reference cost and landed cost review.
- Barcode/QR generation workflow review.
- Label template management usability.
- Product, shelf, and promotion label workflow review.
- Promotion setup and lifecycle polish.
- Promotion visibility at POS.
- Below-cost warning and override review.
- Inventory adjustment clarity.
- Stock movement traceability and audit review.

## 7. Out Of Scope

- Multi-warehouse architecture.
- Multi-store stock transfer.
- Advanced procurement module.
- Full drag-and-drop label designer.
- Accounting integration.
- Complex promotion campaign engine.
- New POS payment methods.
- Authentik/OIDC changes.
- Global role-model changes.

## 8. Dependencies

- Stable V7 UI polish.
- Current inventory, catalog, labels, promotion, audit, and permission models.
- Current barcode/QR generation behavior.
- Current batch upload stock-in service reuse.

## 9. Risks

| Risk | Mitigation |
| --- | --- |
| Inventory polish accidentally changes stock math. | Keep service changes explicit and heavily tested. |
| Label changes fail on physical printers. | Require print checks on real hardware before release. |
| Promotion visibility changes confuse cashier pricing. | Test POS promotion display and below-cost guardrails. |
| Cost visibility leaks to unauthorized users. | Run cost visibility and role tests. |

## 10. Success Criteria

- Owner/manager can understand stock condition quickly.
- Inventory staff can receive and adjust stock with less confusion.
- Label printing is easier to prepare and verify.
- Promotions are easier to set up and audit.
- Below-cost behavior remains safe.
- Stock movement remains traceable.

## 11. Task Groups

- V8-001 Inventory workflow audit.
- V8-002 Stock batch list/detail improvement plan.
- V8-003 Expiry and low-stock operational flow.
- V8-004 Supplier/product cost visibility review.
- V8-005 Barcode/QR workflow polish.
- V8-006 Label template management polish.
- V8-007 Product/shelf/promotion label workflow.
- V8-008 Promotion setup and lifecycle polish.
- V8-009 POS promotion visibility and below-cost review.
- V8-010 Inventory audit and movement traceability review.
- V8-011 V8 QA and release preparation.

## 12. Testing Focus

- Inventory service and movement tests.
- Label route/render/print-preview tests.
- Promotion pricing and below-cost tests.
- Permission/cost visibility tests.
- Manual physical print and scanner/code checks.

## 13. Release Criteria

- Approved V8 tasks are complete or intentionally deferred.
- Stock-changing behavior has tests if touched.
- Label/promotion pages pass route/render checks.
- Physical print verification is recorded when label output changes.
- V8 release note finalized.

## 14. Handoff Notes

V8 can include implementation tasks, but each one must preserve batch-level inventory and audit rules. Do not simplify stock workflows by bypassing `receive_stock()` or movement/audit creation.

V8 closed without database migrations. Physical printer output is the only remaining `Needs Verification` item and should be checked on real label hardware before changing production label stock/templates.
