# Melodu POS Current System Map

Status: Implemented (documentation)
Last updated: 2026-06-17

This document is the product-level map of the existing Melodu POS system. It is based on the current source code (`app/`), URL configuration, settings, templates, services, management commands, scripts, and existing documentation.

When documents overlap, use this map first, then follow the documentation read order in `docs/product/11_DOCUMENTATION_MAP.md`. This document follows `docs/STANDARD_WAY_OF_WORKING.md` as the process authority.

## System Summary

Melodu POS is a Django 5.2 monolith for Melodu Pet Store. It combines point of sale, batch-level inventory, catalog management, batch upload, labels, reports, audit logs, user/capability control, optional Authentik/OIDC login, and optional MinIO/S3-compatible media storage.

| Area | Current State | Notes |
| --- | --- | --- |
| Application style | Current | Django monolith with Django templates and vanilla JavaScript. |
| Database | Current | PostgreSQL through Django ORM. |
| Runtime | Current | Docker Compose with Gunicorn/Django. |
| Public proxy | Current | Host Nginx is expected to terminate HTTPS and proxy to Django. |
| Static files | Current | WhiteNoise with collected static files. |
| Media files | Current | Local filesystem by default; optional MinIO/S3 storage through Django storage backend. |
| Authentication | Current | Local Django login by default; Authentik/OIDC optional. |
| Authorization | Current | Role plus capability model with legacy Admin/Cashier compatibility. |
| Daily UI | Current | Melodu Dashboard under `/dashboard/`. |
| Raw admin UI | Current | Django Admin remains available under `/admin/`. |
| Scanner | Mostly Current | Camera, image upload decode, manual fallback, and read-only resolver exist. Phone/browser behavior remains deployment and device dependent. |
| Documentation | Current | Organized under `docs/product/`, `docs/versions/`, `docs/guides/`, `docs/operations/`, `docs/reference/`, `docs/legacy/`, and `docs/decisions/`. |
| Automated tests | Current | ~297 test methods across 10 custom apps (see Test Coverage). |

## Primary Interfaces

Capability gates below refer to decorators in `app/core/permissions.py` and the
canonical keys in `app/core/capabilities.py`. Owner-tier roles (`is_owner=True`)
implicitly hold every capability.

| Interface | Route | Capability / gate | Status |
| --- | --- | --- | --- |
| Dashboard home | `/dashboard/` | `dashboard_required` (any recognised role) | Current |
| Local login | `/dashboard/login/` | Public when local login enabled | Current |
| Logout | `/dashboard/logout/` | Authenticated staff | Current |
| Django Admin | `/admin/` | Django staff; cashiers blocked by middleware | Current |
| Health check | `/health/` | Infrastructure checks | Current |
| Protected media | `/media/<path>` | Authenticated staff | Current |
| POS | `/dashboard/pos/` | `pos.access` | Current |
| Receipt | `/dashboard/pos/receipt/<sale_id>/` | `pos.access` | Current |
| Receipt reprint | `/dashboard/sales/<sale_id>/reprint/` | `sales.reprint` | Current |
| Sales history | `/dashboard/sales/` | `sales.view_history` | Current |
| Sale detail/cancel | `/dashboard/sales/<id>/`, `/dashboard/sales/<id>/cancel/` | `sales.view_history` / `sales.cancel` | Current |
| Products | `/dashboard/products/` (+ `/new/`, `/<id>/edit/`) | `catalog.manage` | Current |
| Categories | `/dashboard/categories/` (+ CRUD) | `catalog.manage` | Current |
| Brands | `/dashboard/brands/` (+ CRUD) | `catalog.manage` | Current |
| Animal types | `/dashboard/animal-types/` (+ CRUD) | `catalog.manage` | Current |
| Suppliers | `/dashboard/suppliers/` (+ CRUD) | `catalog.manage` | Current |
| Reference costs | `/dashboard/reference-costs/` (+ CRUD) | `catalog.manage` + cost visibility | Current |
| Stock overview | `/dashboard/inventory/` | `inventory.manage` | Current |
| Batch detail | `/dashboard/inventory/batches/<id>/` | `inventory.manage` | Current |
| Receive stock | `/dashboard/stock-in/` | `inventory.manage` | Current |
| Batch upload | `/dashboard/batch-upload/` (+ job/row routes) | `catalog.manage` | Current |
| Barcode/QR print | `/dashboard/barcode-print/` | `inventory.manage` | Current |
| Label templates | `/dashboard/labels/templates/` (+ CRUD) | `catalog.manage` | Current |
| Product labels | `/dashboard/labels/print/` | `inventory.manage` | Current |
| Promotion labels | `/dashboard/labels/promotions/` | `inventory.manage` | Current |
| Promotions | `/dashboard/promotions/` (+ CRUD) | `promotions.manage` | Current |
| Reports | `/dashboard/reports/` (+ sub-reports) | `reports.view` | Current |
| Audit logs | `/dashboard/audit-logs/` | `system.view_audit` | Current |
| Live logs | `/dashboard/live-logs/` | `system.view_logs` | Current |
| System health | `/dashboard/system-health/` | `system.view_logs` | Current |
| Users | `/dashboard/users/` (+ CRUD) | `system.manage_users` | Current |
| Roles | `/dashboard/roles/` (+ CRUD) | Owner only (`owner_required`) | Current |
| Store settings | `/dashboard/settings/` | `system.manage_settings` | Current |
| Auth settings | `/dashboard/auth-settings/` | Owner only (`owner_required`) | Current |
| Style guide | `/dashboard/styleguide/` | Owner or Manager (`admin_required`) | Current |
| Scan resolver API | `/dashboard/api/scan/resolve/` | `dashboard_required` | Current |
| Scan image decode API | `/dashboard/api/scan/decode-image/` | `dashboard_required` | Mostly Current |
| Catalog quick-create API | `/dashboard/api/catalog/quick-create/` | `catalog.manage` | Current |
| OIDC routes | `/oidc/` | OIDC deployments | Current when `AUTH_MODE=oidc` |

## Capability Registry

Authoritative source: `app/core/capabilities.py`.

| Group | Capability key | Label |
| --- | --- | --- |
| POS & sales | `pos.access` | Use the POS screen and create sales |
| POS & sales | `pos.override_below_cost` | Approve a below-cost sale |
| POS & sales | `sales.view_history` | View sales history |
| POS & sales | `sales.cancel` | Cancel a completed sale |
| POS & sales | `sales.reprint` | Reprint a receipt |
| Catalog & inventory | `catalog.manage` | Manage products, categories, brands, suppliers |
| Catalog & inventory | `promotions.manage` | Manage promotions |
| Catalog & inventory | `inventory.manage` | Receive and manage stock, print labels |
| Reports | `reports.view` | View and export reports |
| System | `system.manage_users` | Manage users and role assignments |
| System | `system.manage_settings` | Manage store settings |
| System | `system.view_audit` | View audit logs |
| System | `system.view_logs` | View system health and live logs |
| System | `system.reset_data` | Reset or clear business data |

Built-in role seeds (`BUILTIN_ROLES`): OWNER (all capabilities), MANAGER (most),
INVENTORY (`inventory.manage` only), CASHIER (`pos.access` only), VIEWER
(`sales.view_history`, `reports.view`).

Special rules not stored as capability keys:

- Role matrix CRUD and auth settings: Owner only (`owner_required`).
- Cost visibility: Owner always; others per `StoreSetting.cost_visible_roles`.

## Applications And Ownership

| Django App | Responsibility | Important Models / Services | Status |
| --- | --- | --- | --- |
| `accounts` | Role model, staff profile, OIDC backend, user setup commands | `Role`, `StaffProfile`, `MeloduOIDCBackend`, `setup_roles`, `set_user_role` | Current |
| `audit` | Immutable business/security audit trail | `AuditLog`, `create_audit_log()` helper | Current |
| `batch_upload` | Staged CSV/XLSX import for safe bulk operations | `BatchUploadJob`, `BatchUploadRow`, upload services/views | Current |
| `catalog` | Product and reference master data | `Category`, `Brand`, `Supplier`, `SupplierProductCost`, `ProductTag`, `AnimalTypeOption`, `Product` | Current |
| `core` | Dashboard shell, settings, permissions, scanner APIs, reset command | `StoreSetting`, `AuthSetting`, capability helpers, `reset_business_data` | Current |
| `inventory` | Batch-level stock control and movement ledger | `StockBatch`, `InventoryMovement`, `receive_stock()` | Current |
| `labels` | Product, shelf, promotion, and custom label templates | `LabelTemplate` | Current |
| `pos` | Sales, sale items, promotions, receipt and cancellation workflows | `Promotion`, `Sale`, `SaleItem`, sale services/views | Current |
| `reports` | HTML business reports | Report views and templates | Current |
| `system_logs` | Runtime log viewing and system troubleshooting | Log views | Current |

**Project package (not a Django app):** `melodu_pos` — settings, root URL routing,
WSGI. Lives at `app/melodu_pos/`, not in `INSTALLED_APPS`.

## Business Data Model

The core inventory rule remains batch-level stock integrity.

| Entity | Role | Status |
| --- | --- | --- |
| `Product` | Master product data only; not directly sellable stock. | Current |
| `StockBatch` | Sellable stock unit, with quantity, expiry, supplier, custom code, barcode, QR, and status. | Current |
| `Sale` | Completed/cancelled retail transaction header. | Current |
| `SaleItem` | Line item linked to a product and exact `StockBatch`. | Current |
| `InventoryMovement` | Ledger row for every stock change. | Current |
| `AuditLog` | Security/business audit row for critical actions. | Current |
| `BatchUploadJob` / `BatchUploadRow` | Staged upload state for preview/edit/delete/commit. | Current |
| `Role` / `StaffProfile` | Capability-driven authorization. | Current |
| `StoreSetting` / `AuthSetting` | Singleton operational settings. | Current |

**Not implemented:** `Sale.Status.REFUNDED` and `AuditLog.Action.REFUND` exist in
models but no refund view or service was found in the codebase.

## Gaps, Duplication, And Later Work

| Area | Status | Notes |
| --- | --- | --- |
| Refund workflow | Future / Proposed | Model enums exist; no UI/service |
| Payment gateway integration | Future / Proposed | Payment method recorded only |
| Multi-store inventory | Future / Proposed | Single-store model today |
| Offline POS | Future / Proposed | Requires server/database |
| Report export (CSV/PDF) | Future / Proposed | HTML reports only |
| Full Khmer translation | Needs Verification | i18n exists; coverage incomplete |
| Phone scanner matrix | Needs Verification | Device/browser dependent |
| Physical printer certification | Needs Verification | Browser print only |
| MinIO media migration | Needs Verification | Not automatic from filesystem |
| Backup/restore rehearsal | Needs Verification | Scripts exist; clone test needed |
| Legacy phase docs | Duplicate / Overlapping | `docs/legacy/` — use product docs first |
| `docs/reference/PROJECT_SPEC.md` | Duplicate / Overlapping | Phase 0–11 history; use `05_BRD`/`06_PRD` |
| Route label "Stock-In" vs "Receive Stock" | Needs Verification | Code uses `stock-in`; UX prefers Receive Stock |

**Keep:** batch-level inventory, capability auth, dashboard shell, audit trail,
staging batch upload, OIDC option, MinIO option.

**Rename later (UX only):** inconsistent nav labels — V7 task track.

**Redesign later:** report engine, multi-store schema — V9/V10 planning only.

**Deprecate later:** reliance on Django Admin for daily work — already discouraged.

## Core Business Rules

| Rule | Status | Notes |
| --- | --- | --- |
| Products are master data, not sellable stock | Current | Sales choose stock batches. |
| Stock changes must create inventory movement rows | Current | Stock-in, sale, cancellation, adjustment, damage/expiry workflows use movement records. |
| Critical actions must create audit logs | Current | Login, stock, sale, print, reset, role/settings and permission events are audited. |
| Stock must not go negative | Current | Model constraints and services guard negative quantities. |
| Money fields use Decimal | Current | Price and cost fields are DecimalFields. |
| Stock-in uses batch number and custom code generation | Current | Batch format and custom Melodu code are implemented. |
| Product original barcode uniqueness is enforced | Current | Nullable/blank barcode support exists. |
| Sale cancellation restores stock to original batch | Current | Cancellation workflow reverses stock. |
| Uploads must stage and preview before commit | Current | Applies to supported batch upload targets. |
| POS sales, audit logs, reports, and system logs are not importable | Current | Controlled workflow records stay generated by the app. |

## Authentication And Authorization

| Topic | Status | Notes |
| --- | --- | --- |
| Local Django login | Current | Default mode through `AUTH_MODE=local`. |
| Authentik/OIDC | Current | Optional through `AUTH_MODE=oidc` and `mozilla_django_oidc`. |
| Emergency local login | Current | Controlled by `LOCAL_LOGIN_ENABLED`. |
| OIDC group sync | Current | Groups map to Melodu roles when OIDC sync is enabled. |
| Capability model | Current | Data-driven role capabilities plus user overrides. |
| Legacy Admin/Cashier groups | Current | Compatibility layer maps groups to modern roles. |
| Cashier Django Admin blocking | Current | Middleware blocks cashier access to Django Admin. |
| Final production OIDC claim behavior | Needs Verification | Verify actual Authentik group claim shape on the VPS before relying on sync. |

## Media And Storage

| Mode | Status | Notes |
| --- | --- | --- |
| Local media | Current | `USE_S3_MEDIA=False`; files live under `data/media`. |
| MinIO/S3 media | Current | `USE_S3_MEDIA=True`; Django stores media in S3-compatible backend. |
| Static assets | Current | WhiteNoise serves collected static files. |
| Existing media migration to MinIO | Needs Verification | Existing filesystem media is not automatically migrated. |
| Public media domain and HTTPS | Needs Verification | Production host Nginx must expose the chosen MinIO/media endpoint safely. |

## Scanner And Codes

| Capability | Status | Notes |
| --- | --- | --- |
| Manual code entry | Current | Used as fallback everywhere scanner buttons exist. |
| Camera scanner modal | Mostly Current | Requires localhost or HTTPS and browser camera permission. |
| Uploaded barcode/QR image decode | Mostly Current | Works through dashboard decode API; phone behavior can vary by browser and image quality. |
| Scan resolver API | Current | Read-only resolver; does not mutate stock or sales data. |
| Retail scanner hardware typing into fields | Needs Verification | Should work as keyboard input, but real device testing is needed. |
| Phone camera/upload across target devices | Needs Verification | Continue device testing on production phones. |

## Operational Commands And Scripts

| Area | Command / Script | Status |
| --- | --- | --- |
| Role setup | `python manage.py setup_roles` | Current |
| Set user role | `python manage.py set_user_role` | Current |
| Expire batches | `python manage.py expire_batches` | Current |
| Data reset | `python manage.py reset_business_data` | Current |
| Database backup | `scripts/backup_db.sh` | Current |
| Database restore | `scripts/restore_db.sh` | Current |
| Filesystem media backup | `scripts/backup_media.sh` | Current |
| Filesystem media restore | `scripts/restore_media.sh` | Current |
| MinIO backup | `scripts/backup_minio.sh` | Current |
| MinIO restore | `scripts/restore_minio.sh` | Current |

## Test Coverage

Automated tests live in per-app `tests.py` files (and `tests_oidc.py`,
`tests_cost_visibility.py` under `core/`).

| App | Approx. test methods | Status |
| --- | --- | --- |
| `core` | 65 | Current |
| `pos` | 45 | Current |
| `accounts` | 64 | Current |
| `catalog` | 42 | Current |
| `inventory` | 23 | Current |
| `batch_upload` | 21 | Current |
| `labels` | 11 | Current |
| `reports` | 11 | Current |
| `audit` | 9 | Current |
| `system_logs` | 6 | Current |
| **Total** | **~297** | Current |

Run the full suite:

```bash
docker compose run --rm web python manage.py test
```

## Existing Documentation Status

| Document Area | Status | Notes |
| --- | --- | --- |
| Standard way of working | Current | `docs/STANDARD_WAY_OF_WORKING.md` is the first-read governance doc. |
| Current status | Current | `docs/CURRENT_STATUS.md` remains the compact handoff. |
| Design system | Current | `docs/DESIGN_SYSTEM.md` remains authoritative for UI style. |
| Docs folder index | Current | `docs/README.md` maps all subfolders. |
| V6 docs | Current | Foundation reset and auth/OIDC docs under `docs/versions/v6/`. |
| Guides | Current | `docs/guides/` |
| Operations | Current | `docs/operations/` |
| Reference | Current | `docs/reference/` |
| Legacy phase docs | Mostly Current | `docs/legacy/` — supporting history only. |
| Product-level BRD/PRD/TRD | Current | `docs/product/` |
| ADR set | Current | `docs/decisions/` |
| Historical V1–V5 | Implemented | `docs/versions/v1/`–`v5/`; legacy in `docs/legacy/` |

## Needs Verification Register

These items should be verified during the next production QA pass.

| Item | Why It Matters | Owner |
| --- | --- | --- |
| Authentik group claim payload and role sync in production | Prevents accidental missing or wrong staff access. | Human + AI |
| Host Nginx app and media domain configuration | CSRF, secure cookies, camera access, and media URLs depend on correct HTTPS proxy headers. | Human + AI |
| MinIO migration of existing `data/media` files | Prevents lost product/store/label/barcode images after enabling object storage. | Human + AI |
| Phone scanner camera and upload decode on production devices | Scanner performance is device/browser/image dependent. | Human + AI |
| Receipt and label output on real printers | Browser rendering can differ from physical thermal/label printer output. | Human |
| Backup/restore rehearsal against a non-production clone | Confirms the recovery path before real incident response. | Human + AI |
