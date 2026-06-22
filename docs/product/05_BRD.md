# Business Requirements Document

Status: Current
Last updated: 2026-06-16

## Purpose

This BRD describes the business needs Melodu POS must satisfy. It reflects the current build and marks future needs without implementing them.

## Business Objectives

| ID | Objective | Status | Success Signal |
| --- | --- | --- | --- |
| BRD-OBJ-001 | Operate daily pet-store sales from a clean dashboard instead of raw Django Admin. | Current | Cashier can complete sales from `/dashboard/pos/`. |
| BRD-OBJ-002 | Maintain reliable batch-level inventory with expiry visibility. | Current | Stock-in, sale, cancellation, adjustment, and expiry records are traceable. |
| BRD-OBJ-003 | Reduce manual data entry through scanning, labels, and batch upload. | Mostly Current | Scanner and upload workflows exist; phone scanner behavior needs verification. |
| BRD-OBJ-004 | Keep manager/owner control over users, roles, reports, logs, and settings. | Current | Capability-gated dashboard pages exist. |
| BRD-OBJ-005 | Make production operations recoverable through documentation and backup scripts. | Mostly Current | Runbooks/scripts exist; recovery rehearsal still needs verification. |

## Stakeholders

| Stakeholder | Needs | Status |
| --- | --- | --- |
| Store owner | Full visibility, user control, audit trail, backup/recovery path. | Current |
| Manager | Manage catalog, inventory, sales history, reports, and daily exceptions. | Current |
| Cashier | Fast selling flow with simple scan/manual entry and receipt access. | Current |
| Inventory staff | Receive stock, print labels, track expiry and adjustments. | Current |
| Accountant/operator | Exportable or inspectable sales and movement data. | Mostly Current |
| AI/human development team | Clear source-of-truth docs and disciplined change process. | Current after this reset |

## Functional Business Requirements

| ID | Requirement | Priority | Status |
| --- | --- | --- | --- |
| BRD-CAT-001 | Maintain products, categories, brands, suppliers, animal types, tags, and reference costs. | High | Current |
| BRD-CAT-002 | Enforce unique product codes and original barcode rules. | High | Current |
| BRD-CAT-003 | Store product images reliably. | High | Current |
| BRD-CAT-004 | Support multiple animal types per product. | Medium | Current |
| BRD-CAT-005 | Let admin users create animal types from dashboard workflows. | Medium | Current |
| BRD-INV-001 | Receive stock into batches with quantity, cost, price, supplier, expiry, and codes. | High | Current |
| BRD-INV-002 | Prevent negative stock. | High | Current |
| BRD-INV-003 | Record every stock change as an inventory movement. | High | Current |
| BRD-INV-004 | Show expiry risk and damaged/expired states. | High | Current |
| BRD-INV-005 | Support stock adjustments only with a reason. | High | Current |
| BRD-POS-001 | Complete sales from selected stock batches. | High | Current |
| BRD-POS-002 | Support scanner/manual product lookup. | High | Mostly Current |
| BRD-POS-003 | Support receipt view/reprint. | High | Current |
| BRD-POS-004 | Support sale cancellation with reason and stock reversal. | High | Current |
| BRD-POS-005 | Support promotions and below-cost guardrails. | Medium | Current |
| BRD-UPL-001 | Upload supported master data from CSV/XLSX with preview. | Medium | Current |
| BRD-UPL-002 | Upload stock-in rows through the existing receiving service. | High | Current |
| BRD-UPL-003 | Exclude generated/controlled records from upload. | High | Current |
| BRD-LBL-001 | Generate and print barcode/QR labels for stock batches. | High | Current |
| BRD-LBL-002 | Manage reusable label templates. | Medium | Current |
| BRD-RPT-001 | Provide sales, stock, low stock, expiry, movement, and staff sales reports. | High | Current |
| BRD-SEC-001 | Restrict dashboards by role/capability. | High | Current |
| BRD-SEC-002 | Support local and optional Authentik/OIDC authentication. | High | Current |
| BRD-AUD-001 | Audit critical operations. | High | Current |
| BRD-OPS-001 | Provide live logs and system health pages. | Medium | Current |
| BRD-OPS-002 | Provide backup and restore commands/docs. | High | Mostly Current |

## Non-Functional Business Requirements

| ID | Requirement | Status | Notes |
| --- | --- | --- | --- |
| BRD-NFR-001 | Use Decimal for money, never float. | Current | Implemented with DecimalFields and Decimal workflows. |
| BRD-NFR-002 | Use database transactions for stock-changing workflows. | Current | Must remain protected in future changes. |
| BRD-NFR-003 | Keep daily UI mobile-friendly. | Mostly Current | Requires ongoing phone verification. |
| BRD-NFR-004 | Keep sensitive logs/secrets out of dashboard log output. | Mostly Current | Needs ongoing production review. |
| BRD-NFR-005 | Keep documentation current with changes. | Current | Formalized by Standard Way of Working and ADR-0007. |
| BRD-NFR-006 | Support Khmer and English UI direction. | Mostly Current | Language switch exists; translation completeness may need review. |

## Out Of Scope For Current Build

| Item | Status | Notes |
| --- | --- | --- |
| External payment gateway integration | Future / Proposed | Current payment methods are recorded, not gateway-processed. |
| Native mobile app | Future / Proposed | Current mobile use is through browser. |
| Offline POS mode | Future / Proposed | Current workflows require server/database access. |
| Multi-store or warehouse transfer logic | Future / Proposed | Current system is single-store oriented. |
| Accounting system integration | Future / Proposed | Reports are HTML/dashboard based. |
| Customer loyalty/CRM | Future / Proposed | Not implemented in current source map. |

## Open Business Questions

| Question | Status |
| --- | --- |
| Which production phones and browsers must pass scanner QA? | Needs Verification |
| What is the final media domain and retention policy for MinIO? | Needs Verification |
| Which reports become official financial records versus operational dashboards? | Needs Verification |
| What exact approval rule should apply to below-cost selling in production? | Needs Verification |
