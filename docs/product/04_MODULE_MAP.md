# Module Map

Status: Implemented (documentation)
Last updated: 2026-06-17

This map explains each major product module, where it lives, who uses it, and what rules must be preserved.

## Module Summary

| Module | Code Area | Main Routes | Main Users | Status |
| --- | --- | --- | --- | --- |
| Authentication | `accounts`, `core`, `melodu_pos/settings.py` | `/dashboard/login/`, `/dashboard/logout/`, `/oidc/` | All staff | Current |
| Authorization | `accounts`, `core.permissions`, `core.capabilities` | All dashboard routes | All staff | Current |
| Dashboard Shell | `core`, templates, static assets | `/dashboard/`, shared layout | All staff | Current |
| Catalog | `catalog` | `/dashboard/products/`, categories, brands, suppliers, animal types | Owner, Manager, Inventory | Current |
| Batch Upload | `batch_upload` | `/dashboard/batch-upload/` | Staff with `catalog.manage` | Current |
| Inventory | `inventory` | `/dashboard/inventory/`, `/dashboard/stock-in/` | Owner, Manager, Inventory | Current |
| POS | `pos` | `/dashboard/pos/`, receipt routes | Cashier, Manager, Owner | Current |
| Sales Admin | `pos` | `/dashboard/sales/` | Manager, Owner, Viewer | Current |
| Promotions | `pos` | `/dashboard/promotions/` | Manager, Owner | Current |
| Labels | `labels`, inventory print views | `/dashboard/barcode-print/`, `/dashboard/labels/` | `inventory.manage` / `catalog.manage` for templates | Current |
| Reports | `reports` | `/dashboard/reports/` | Owner, Manager, Viewer | Current |
| Audit | `audit` | `/dashboard/audit-logs/`, Django Admin | Owner, Manager | Current |
| System Logs/Health | `system_logs`, `core` | `/dashboard/live-logs/`, `/dashboard/system-health/` | Owner, Manager | Current |
| Store Settings | `core` | `/dashboard/settings/`, `/dashboard/auth-settings/` | `system.manage_settings` / Owner for auth settings | Current |
| Backups/Restore | scripts and docs | CLI scripts | Owner/operator | Current |

## Authentication Module

| Field | Details |
| --- | --- |
| Purpose | Let staff authenticate through local Django login or optional Authentik/OIDC. |
| Key files | `app/melodu_pos/settings.py`, `app/accounts/oidc.py`, `app/core/views.py`, `app/core/models.py` |
| Data | Django `User`, `AuthSetting`, `StaffProfile`, `Role` |
| Controls | `AUTH_MODE`, `LOCAL_LOGIN_ENABLED`, OIDC env vars, Authentik group mapping, `AuthSetting.local_login_enabled` |
| Status | Current |
| Risks | OIDC group claims and logout behavior require production verification. |

## Authorization Module

| Field | Details |
| --- | --- |
| Purpose | Enforce role/capability boundaries across dashboard and sensitive actions. |
| Key files | `app/core/permissions.py`, `app/core/capabilities.py`, `app/accounts/models.py` |
| Role tiers | Owner, Manager, Inventory Staff, Cashier, Viewer |
| Capability source | `app/core/capabilities.py` (keys), `accounts.Role` (grants), `StaffProfile` (overrides) |
| Compatibility | Legacy Admin/Cashier groups still map to modern roles. |
| Status | Current |
| Risks | New views must use capability decorators; Django Admin exposure must stay controlled. |

## Dashboard Shell

| Field | Details |
| --- | --- |
| Purpose | Provide daily work UI separate from Django Admin. |
| Key files | `app/templates/dashboard/base.html`, dashboard templates, static dashboard CSS/JS |
| Features | Sidebar, mobile nav, top action bar, role-aware navigation, language switch, scanner modal |
| Status | Current |
| Design authority | `docs/DESIGN_SYSTEM.md` |
| Risks | UI changes must follow the design system and be verified on desktop/mobile. |

## Catalog Module

| Field | Details |
| --- | --- |
| Purpose | Maintain product master data and supplier/reference data. |
| Key models | `Category`, `Brand`, `Supplier`, `SupplierProductCost`, `AnimalTypeOption`, `ProductTag`, `Product` |
| Key workflows | Product CRUD, product image upload, classification, barcode fields, supplier cost references |
| Upload support | Categories, brands, suppliers, products |
| Status | Current |
| Risks | Barcode uniqueness and product image storage must remain reliable. |

## Batch Upload Module

| Field | Details |
| --- | --- |
| Purpose | Safely import supported CSV/XLSX data through staging and preview. |
| Key models | `BatchUploadJob`, `BatchUploadRow` |
| Gate | `@catalog_required` → `catalog.manage` |
| Supported targets | Categories, brands, suppliers, products, stock-in |
| Excluded targets | POS sales, audit logs, reports, system logs |
| Commit style | Master data update-or-create; stock-in uses `receive_stock()` |
| Status | Current |
| Risks | Upload validation must not bypass services or stock/audit rules. |

## Inventory Module

| Field | Details |
| --- | --- |
| Purpose | Control stock by batch and keep a movement ledger. |
| Key models | `StockBatch`, `InventoryMovement` |
| Key services | `receive_stock()`, adjustment/cancellation workflows |
| Batch rule | StockBatch is the sellable stock unit. |
| Status | Current |
| Risks | Negative stock prevention and transaction boundaries are high risk. |

## POS And Sales Module

| Field | Details |
| --- | --- |
| Purpose | Sell stock safely, record payments, receipts, promotions, and cancellations. |
| Key models | `Sale`, `SaleItem`, `Promotion` |
| Key routes | `/dashboard/pos/`, `/dashboard/pos/receipt/<id>/`, `/dashboard/sales/<id>/reprint/` |
| Key rule | Every `SaleItem` links to an exact `StockBatch`. |
| Status | Current |
| Risks | Price/cost snapshots, below-cost overrides, and cancellation reversal must stay consistent. |

## Labels Module

| Field | Details |
| --- | --- |
| Purpose | Print barcode/QR, product, shelf, promotion, and custom labels. |
| Key model | `LabelTemplate` |
| Gates | `inventory.manage` for print flows; `catalog.manage` for template CRUD |
| Output | Browser print layouts and stored barcode/QR images. |
| Status | Current |
| Risks | Real printer output needs device-specific verification. |

## Reports Module

| Field | Details |
| --- | --- |
| Purpose | Provide simple HTML business reports. |
| Reports | Daily sales, stock summary, low stock, expiry, stock movement, staff sales |
| Status | Current |
| Risks | Report business definitions should be reviewed before relying on financial close. |

## Audit And System Module

| Field | Details |
| --- | --- |
| Purpose | Make operational actions traceable and production issues diagnosable. |
| Key model | `AuditLog` |
| Key pages | Audit logs, live logs, system health |
| Status | Current |
| Risks | Logs must avoid secrets; production log rotation policy needs verification. |

## Backup And Deployment Module

| Field | Details |
| --- | --- |
| Purpose | Support VPS deployment and recovery. |
| Key files | `docker-compose.prod.yml`, scripts, deployment docs, backup docs |
| Status | Mostly Current |
| Risks | Backup/restore rehearsal and MinIO media migration need verification. |
