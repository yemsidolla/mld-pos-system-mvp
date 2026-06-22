# Product Requirements Document

Status: Current
Last updated: 2026-06-16

## Purpose

This PRD translates the business requirements into product behavior. It records current behavior, known verification gaps, and future work without changing the application.

## Personas

| Persona | Primary Goal | Key UX Needs | Status |
| --- | --- | --- | --- |
| Owner | Control the business and system safely. | Full access, audit trails, settings, recovery docs. | Current |
| Manager | Run daily operations. | Fast catalog/inventory/sales tools and clear reports. | Current |
| Inventory staff | Keep stock accurate. | Receive stock, print labels, adjust with reasons, see expiry. | Current |
| Cashier | Complete sales quickly. | POS-focused UI, scan/manual entry, receipt access. | Current |
| Viewer | Inspect reports and sales. | Read-only navigation. | Current |

## Product Requirements

| ID | Feature | User Story | Acceptance | Status |
| --- | --- | --- | --- | --- |
| PRD-AUTH-001 | Local login | As staff, I can log in with a local account when enabled. | Authenticated users enter the dashboard; inactive users cannot proceed. | Current |
| PRD-AUTH-002 | OIDC login | As a deployed store, staff can authenticate through Authentik. | OIDC routes work when `AUTH_MODE=oidc`; roles can sync from configured groups. | Current |
| PRD-AUTH-003 | Emergency local login | As owner, I can retain local login during OIDC rollout. | `LOCAL_LOGIN_ENABLED` controls local fallback. | Current |
| PRD-AUTH-004 | Role/capability navigation | As staff, I only see pages I am allowed to use. | Dashboard nav is capability-aware. | Current |
| PRD-AUTH-005 | Django Admin protection | As owner, cashier users cannot access Django Admin by mistake. | Cashier admin block middleware denies admin access. | Current |
| PRD-CAT-001 | Product management | As manager, I can create/edit products with code, barcode, price, cost, category, brand, image, and classification. | Product list/form pages exist and audit important changes. | Current |
| PRD-CAT-002 | Animal type management | As manager, I can create animal types and assign multiple types to a product. | `/dashboard/animal-types/` and product M2M fields exist. | Current |
| PRD-CAT-003 | Supplier/reference cost management | As manager, I can manage suppliers and product cost references. | Supplier and reference cost pages exist. | Current |
| PRD-UPL-001 | Batch upload staging | As admin, I can upload CSV/XLSX and preview rows before commit. | Job/row staging persists across refresh. | Current |
| PRD-UPL-002 | Preview row correction | As admin, I can edit/delete rows before commit. | Preview supports row edit/delete/skip behavior. | Current |
| PRD-UPL-003 | Stock-in upload service reuse | As admin, uploaded stock-in rows create batches through `receive_stock()`. | Batch, code images, movements, and audits are created consistently. | Current |
| PRD-INV-001 | Receive stock | As inventory staff, I can receive stock into a batch. | Batch number/custom code/barcode/QR/movement/audit created. | Current |
| PRD-INV-002 | Stock overview | As inventory staff, I can search products/batches and see current stock. | Inventory dashboard lists summaries and batches. | Current |
| PRD-INV-003 | Batch detail and adjustment | As manager, I can inspect a batch and adjust stock with a reason. | Adjustment cannot create negative stock and leaves movement/audit. | Current |
| PRD-INV-004 | Expiry control | As manager, I can identify expired/critical/warning stock. | Expiry statuses and `expire_batches` command exist. | Current |
| PRD-POS-001 | Sale creation | As cashier, I can scan/type codes, build a cart, and complete a sale. | Sale and items are persisted; stock is deducted from selected batches. | Current |
| PRD-POS-002 | Batch selection | As cashier, original barcode lookup requires exact batch selection when needed. | Sale item links to `StockBatch`. | Current |
| PRD-POS-003 | Promotions | As manager/cashier, active promotions can affect sale pricing. | Promotion model and POS price calculations exist. | Current |
| PRD-POS-004 | Receipt | As cashier, I can view or reprint sale receipts. | Receipt at `/dashboard/pos/receipt/<id>/`; reprint at `/dashboard/sales/<id>/reprint/`. | Current |
| PRD-POS-005 | Cancellation | As manager, I can cancel a sale with reason and restore stock. | Cancellation workflow reverses batches and audits. | Current |
| PRD-SCAN-001 | Reusable scanner modal | As staff, I can use camera, image upload, or manual input where scanning is useful. | Scanner modal and buttons exist in relevant workflows. | Mostly Current |
| PRD-SCAN-002 | Read-only scan resolve | As staff, scanned text resolves metadata without changing data. | Resolver API returns product/batch data and does not mutate records. | Current |
| PRD-LBL-001 | Barcode/QR print | As inventory staff, I can print labels for batches. | Barcode print page and audit log exist. | Current |
| PRD-LBL-002 | Label templates | As manager, I can manage reusable label layouts. | Template CRUD and print flows exist. | Current |
| PRD-RPT-001 | Reports dashboard | As manager, I can view daily sales, stock, low stock, expiry, movement, and staff reports. | Report routes and pages exist. | Current |
| PRD-SYS-001 | Live logs | As manager/operator, I can view backend logs in the dashboard. | Live log page exists and is capability-gated. | Current |
| PRD-SYS-002 | System health | As manager/operator, I can see database/disk/log/last activity checks. | System health page exists. | Current |
| PRD-OPS-001 | Backup and restore | As owner/operator, I can back up and restore database/media. | Scripts and guides exist. | Mostly Current |

## UX Requirements

| Requirement | Status | Authority |
| --- | --- | --- |
| Dashboard, not Django Admin, is the daily working interface. | Current | `docs/DESIGN_SYSTEM.md`, dashboard templates |
| UI should be dense, readable, and work-focused. | Current | `docs/DESIGN_SYSTEM.md` |
| Mobile navigation and scanner affordances are required for daily workflows. | Mostly Current | Dashboard shell and scanner JS |
| The dashboard should support English and Khmer. | Mostly Current | Django i18n settings and locale files |
| Product pages should follow the shared design system. | Current | `docs/DESIGN_SYSTEM.md` |

## Data Requirements

| Data | Requirement | Status |
| --- | --- | --- |
| Products | Unique product code, optional unique original barcode, active status, image, classification. | Current |
| Stock batches | Product, supplier, expiry, quantities, costs, selling price, custom code, barcode, QR. | Current |
| Movements | Every stock change records movement type, quantities, batch, and user context. | Current |
| Sales | Sale header and item records retain price/cost snapshots and batch link. | Current |
| Audits | Critical workflows record user, action, module/object, IP/user-agent when available. | Current |
| Upload staging | Raw, normalized, validation errors, warnings, selected/deleted, commit result. | Current |

## Edge Cases To Preserve

| Edge Case | Expected Behavior | Status |
| --- | --- | --- |
| Blank original barcode on products | Allowed where model rules permit; uniqueness applies to non-empty values. | Current |
| Duplicate upload master data | Update existing stable records instead of creating duplicates. | Current |
| Invalid upload rows | Block commit for invalid rows. | Current |
| Product without original barcode in stock-in upload | Reject stock-in row. | Current |
| Expired stock sale | Should be blocked or excluded by sale service rules. | Current |
| Negative stock attempt | Reject with validation/business error. | Current |
| Missing scanner permission | Show clear fallback/error and allow manual input. | Mostly Current |
| Phone image decode failure | Manual fallback remains available; decode reliability needs device testing. | Needs Verification |

## Future Product Proposals

| ID | Proposal | Status |
| --- | --- | --- |
| PRD-FUT-001 | Official exports for accounting/reporting. | Future / Proposed |
| PRD-FUT-002 | Customer/loyalty profile support. | Future / Proposed |
| PRD-FUT-003 | Multi-store inventory and transfer workflows. | Future / Proposed |
| PRD-FUT-004 | Payment gateway or KHQR transaction verification integration. | Future / Proposed |
| PRD-FUT-005 | Offline-tolerant POS queue. | Future / Proposed |
| PRD-FUT-006 | Barcode scanner hardware certification checklist. | Future / Proposed |
