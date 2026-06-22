# Melodu POS V2 Baseline Audit

Date: 2026-06-09

## 1. Executive Summary

Melodu POS is a Django monolith with PostgreSQL, Gunicorn, WhiteNoise, Docker Compose, and host-level Nginx for production HTTPS/reverse proxy. Version 1 is functionally broad: dashboard master data, POS, stock-in, batch inventory, barcode/QR labels, sale history/cancellation, inventory adjustments, reports, audit logs, live logs, system health, batch upload, English/Khmer i18n, and scanner support.

The current maturity level is a stable V1 MVP with good service-level business rules and a passing automated test suite. The repo is ready for V2 audit/documentation work and V1 stabilization planning. It is not ready for new V2 business features until the V1 stabilization changes are preserved and owner decisions are made for any expanded product scope.

Immediate blockers:

- No critical runtime blocker found in Phase 0A.
- The working tree is intentionally dirty from V1 stabilization and no-internal-Docker-Nginx cleanup; preserve or commit that baseline before starting feature work.
- Production camera scanning requires HTTPS; local LAN HTTP is useful for iPhone manual testing, but camera access may be blocked by mobile browsers.

Phase 0A file-change statement: no files were changed during the read-only audit pass. Phase 0B created documentation from the approved audit plan.

## 2. Repository Snapshot

Current branch: `main`

Recent commits:

```text
ee16149 Add dashboard product management
4c7c51b Add user role assignment command
d1a695f Serve static assets from Django app
9b343a1 Document static serving for external nginx
43b4448 Add external nginx deployment override
```

Current working tree summary:

- Modified V1 stabilization files in catalog, POS, dashboard templates, settings, compose files, and docs.
- Deleted obsolete internal/external-Nginx Docker files: `docker-compose.external-nginx.yml`, `docker/nginx/default.conf`.
- Added dashboard master-data templates and `docker-compose.local.yml`.

Runtime versions observed through Docker:

- Python: `3.12.13`
- Django: `5.2.15`

Dependency/config files found:

- `app/requirements.txt`
- `.env.example`
- `docker-compose.yml`
- `docker-compose.local.yml`
- `docker-compose.prod.yml`
- `docker/django/Dockerfile`

Documentation files found:

- `docs/guides/BACKUP_GUIDE.md`
- `docs/guides/BATCH_UPLOAD_GUIDE.md`
- `docs/reference/CODEX_RULES.md`
- `docs/guides/DASHBOARD_UX_GUIDE.md`
- `docs/guides/DEPLOYMENT_GUIDE.md`
- `docs/DEVELOPMENT_LOG.md`
- `docs/operations/PRODUCTION_CHECKLIST.md`
- `docs/reference/PROJECT_SPEC.md`
- `docs/TASKS.md`
- `docs/guides/TESTING_GUIDE.md`
- `docs/guides/USER_MANAGEMENT_GUIDE.md`

## 3. Django Project Structure

Project: `melodu_pos`

Apps:

| App | Purpose | Main responsibilities |
| --- | --- | --- |
| `accounts` | User role setup and account safety | Role setup command, Cashier/Admin tests, cashier admin block integration |
| `catalog` | Master data | Category, Brand, Supplier, Product models; admin and dashboard CRUD |
| `inventory` | Batch-level stock | Stock-in, StockBatch, InventoryMovement, labels, adjustment, damage, expiry |
| `pos` | Sales | POS scan/cart/confirm, receipt, sale history, cancellation |
| `reports` | HTML reports | Daily sales, stock summary, low stock, expiry, movements, staff sales |
| `audit` | Audit trail | AuditLog model, helper, login success/failure signals |
| `system_logs` | Ops visibility | Live logs, health details, log redaction |
| `batch_upload` | CSV/XLSX import workflow | Upload jobs/rows, preview validation, edit/delete, commit |
| `core` | Shared shell, permissions, scanner, health | Dashboard context, permission helpers, scan resolver, middleware |

Important URL groups:

- `/dashboard/`
- `/dashboard/products/`, `/dashboard/categories/`, `/dashboard/brands/`, `/dashboard/suppliers/`
- `/dashboard/stock-in/`, `/dashboard/inventory/`, `/dashboard/barcode-print/`
- `/dashboard/pos/`, `/dashboard/pos/receipt/<sale_id>/`
- `/dashboard/sales/`, `/dashboard/sales/<sale_id>/cancel/`
- `/dashboard/reports/`
- `/dashboard/batch-upload/`
- `/dashboard/api/scan/resolve/`
- `/dashboard/live-logs/`, `/dashboard/system-health/`
- `/health/`

## 4. Data Model Audit

Catalog:

- `Category`, `Brand`, and `Supplier` are unique-name master-data models with `is_active`.
- `Product` has unique `product_code`, optional unique `original_barcode`, optional category/brand, default prices, `min_stock`, image, and `is_active`.
- Category, Brand, and Supplier are protected from deletion while referenced by products or batches.

Inventory:

- `StockBatch` is the sellable stock unit. It links to product, supplier, and receiver; has batch number, expiry, quantity received/available, prices, generated custom code, barcode/QR images, and status.
- `StockBatch` constraints prevent negative available quantity and non-positive received quantity.
- `StockBatch.clean()` prevents available quantity from exceeding received quantity.
- `InventoryMovement` records stock-in, sale, adjustment, return, damage, and expired movements.

POS:

- `Sale` records sale number, cashier, total/discount/final amount, payment method, status, cancel reason, and timestamps.
- `SaleItem` links each sold item to `Sale`, `Product`, and the exact `StockBatch`.

Audit:

- `AuditLog` stores user, action, module, object identity/display, old/new JSON values, IP, user agent, and timestamp.

Batch upload:

- `BatchUploadJob` stores target, filename, uploader, status, summary, and commit time.
- `BatchUploadRow` stores raw/normalized data, validation errors, warnings, selection/deletion flags, and commit action.

Relationship summary:

```text
Product -> StockBatch -> SaleItem -> Sale
Supplier -> StockBatch
StockBatch -> InventoryMovement
Sale cancellation -> StockBatch quantity restore + InventoryMovement RETURN + AuditLog SALE_CANCEL
Stock-in -> StockBatch + InventoryMovement STOCK_IN + AuditLog STOCK_IN
Batch upload stock-in -> receive_stock() -> normal inventory/audit workflow
```

## 5. Business Rules Found in Code

| Rule | Evidence |
| --- | --- |
| Product master data is active/inactive and product code is unique. | `catalog.models.Product` |
| Original barcode is optional but unique when present. | `catalog.models.Product.original_barcode` |
| Stock-in requires positive quantity, active product, active supplier, expiry date, and original barcode. | `inventory.services.receive_stock()`, `build_custom_code()` |
| Batch numbers use `BYYNNNN`. | `inventory.services.generate_batch_number()` |
| Custom codes use `[original_barcode]-M-[expiry_yymmdd]-[batch_no]`. | `inventory.services.build_custom_code()` |
| Stock changes are transactional for stock-in, adjustment, damage, expiry, sale, cancellation, and upload commit. | `@transaction.atomic` in inventory/POS/batch upload services |
| Sale requires non-empty cart and positive quantities. | `pos.services.confirm_sale()` |
| Expired, inactive, unavailable, or insufficient batches cannot be sold. | `pos.services.validate_sellable_batch()` |
| Sale confirmation deducts batch quantity and marks sold-out batches. | `pos.services.confirm_sale()` |
| Sale cancellation only applies to completed sales and requires reason. | `pos.services.cancel_sale()` |
| Cancellation restores stock to the original batch and creates return movements. | `pos.services.cancel_sale()` |
| Adjustments require reason, non-zero delta, and cannot make stock negative. | `inventory.services.adjust_stock()` |
| Damage and expiry flows require reasons and create movement/audit records. | `inventory.services.mark_batch_damaged()`, `mark_batch_expired()` |
| Cashier users can access POS; Admin/superusers access management pages. | `core.permissions` |
| Cashiers are blocked from Django Admin unless also Admin/superuser. | `core.middleware.CashierAdminBlockMiddleware` |
| Scanner resolver is read-only and returns warnings for inactive/expired/unavailable records. | `core.views.scan_resolve_view()` |
| Batch upload validates rows before commit and never commits invalid selected rows. | `batch_upload.services.commit_upload_job()` |

## 6. POS Flow Audit

The POS page is `/dashboard/pos/` and is protected by `pos_required`.

Flow:

1. Cashier scans or enters a code through `pos_sale_view()`.
2. `scan_code()` routes custom-code scans to exact batch lookup and original barcode scans to product lookup.
3. Custom code adds the exact batch to cart immediately.
4. Original barcode shows sellable batches ordered by expiry date and batch number.
5. Cart rows are stored in session as stock batch IDs and quantities.
6. Cart supports add, update, remove, clear, and confirm.
7. Confirm calls `confirm_sale()` in a transaction.
8. Sale items, batch deductions, sale inventory movements, and `SALE_CREATE` audit log are created.
9. Receipt renders at `/dashboard/pos/receipt/<sale_id>/`.

Risk notes:

- Cart is session-backed, so stale cart rows are validated again at confirm time.
- Discount is validated against total.
- No export/print format beyond HTML receipt was observed.

## 7. Inventory Flow Audit

Stock-in:

- Admin submits `/dashboard/stock-in/`.
- `receive_stock()` validates product/supplier/quantity/expiry/barcode.
- It creates the batch, generates barcode/QR images, creates `STOCK_IN` movement, and writes audit log.

Inventory:

- `/dashboard/inventory/` shows product summaries and batches.
- `/dashboard/inventory/batches/<batch_id>/` supports adjustment, damage, and expiry flows.
- `get_expiry_status()` classifies Expired, Critical, Warning, and Normal.

Risks:

- Reports and summaries use available quantity aggregation; V2 should confirm whether inactive/expired/sold-out batches should be included in each report.
- There is no scheduled expiry job; expiry status is calculated or manually marked.

## 8. Batch Upload Audit

Supported targets:

- Categories
- Brands
- Suppliers
- Products
- Stock-in

Flow:

1. Upload CSV/XLSX.
2. Parse headers and rows.
3. Create database-backed preview job/rows.
4. Normalize and validate rows.
5. Allow row edit/delete before commit.
6. Revalidate before commit.
7. Commit valid selected rows only.
8. Write audit summary after commit.

Important behavior:

- Category/brand/supplier use name as update-or-create key.
- Product uses product code as update-or-create key.
- Stock-in upload uses the existing `receive_stock()` service.
- Invalid, deleted, or unselected rows are not committed.

## 9. Scanner / Barcode / QR Audit

Scanner pieces:

- Shared modal: `dashboard/scanner_modal.html`
- Scanner JS: `core/static/core/js/scanner.js`
- Resolver API: `/dashboard/api/scan/resolve/`
- Vendored library: `core/static/core/vendor/html5-qrcode.min.js`

Behavior:

- Camera, image upload, and manual entry are supported.
- Camera scanning requires secure context; localhost is allowed for development.
- Resolver supports custom code, batch number, product code, and original barcode.
- Resolver is read-only and does not mutate sales, stock, uploads, movements, or audits.

## 10. Reports Audit

Current reports are HTML-only:

- Daily sales: date filter, completed totals, sale list.
- Stock summary: product total available quantities.
- Low stock: products where total available is less than or equal to `min_stock`.
- Expiry: batches expiring within 60 days with status classification.
- Stock movements: latest 300 inventory movements.
- Staff sales: completed sale counts and totals by cashier.

Risk notes:

- No CSV/PDF/export support in V1.
- V2 should decide whether reports should exclude inactive products or non-active batches.

## 11. Permissions & Role Audit

Roles:

- `Admin`: management pages.
- `Cashier`: POS and receipts.
- Superuser: treated as Admin.

Protection:

- `admin_required` wraps management views.
- `pos_required` wraps POS and receipts.
- `CashierAdminBlockMiddleware` blocks cashier-only users from `/admin/`.
- Role-aware navigation hides unavailable links.

Risk notes:

- URL-level decorators are present on audited dashboard views.
- Future V2 APIs should reuse the same permission helpers or introduce explicit permission classes with tests.

## 12. Audit Log & System Log Audit

Audit logs are created for:

- Login success/failure.
- Catalog create/update.
- Stock-in.
- Barcode print.
- Sale create.
- Sale cancel.
- Stock adjustment/damage/expiry.
- Batch upload commit summary.

System logs:

- Python logging writes app and error logs.
- Live logs redact secret-like values before display.
- System health checks database, disk, log writability, last sale, last stock-in, and latest error.

Risk note:

- Log viewer reads local log files directly; production log rotation and retention should stay documented.

## 13. Deployment & Configuration Audit

Deployment shape:

- Local: `docker-compose.yml` + `docker-compose.local.yml`
- Production: `docker-compose.prod.yml`
- Services: `postgres`, `web`
- No internal Docker Nginx service.
- Host Nginx should proxy to the Django/Gunicorn web port.
- WhiteNoise serves collected static files.

Observed validation:

```text
local compose services: postgres, web
prod compose services: postgres, web
local /health/: ok
LAN /health/ at 192.168.1.199:8000: HTTP 200
```

Production safety settings are environment-driven:

- `DJANGO_DEBUG`
- `DJANGO_SECRET_KEY`
- `DJANGO_ALLOWED_HOSTS`
- `DJANGO_CSRF_TRUSTED_ORIGINS`
- `DJANGO_SESSION_COOKIE_SECURE`
- `DJANGO_CSRF_COOKIE_SECURE`
- database credentials

## 14. Test Audit

Test files found:

- `app/accounts/tests.py`
- `app/audit/tests.py`
- `app/batch_upload/tests.py`
- `app/catalog/tests.py`
- `app/core/tests.py`
- `app/inventory/tests.py`
- `app/pos/tests.py`
- `app/reports/tests.py`
- `app/system_logs/tests.py`

Verification result:

```text
python manage.py check: OK
python manage.py test: 99 tests, OK
```

Current critical coverage includes POS scan/cart, sale confirmation, stock deduction, cancellation, inventory movement, audit logging, permissions, scanner resolver, batch upload parse/preview/edit/delete/commit, reports, system health, and secret-safe log display.

Suggested V2 stabilization coverage:

- Browser/mobile smoke checks for dashboard, POS, inventory, and batch upload.
- Backup/restore rehearsal on a non-production copy.
- Report inclusion rules for inactive/expired/sold-out records.
- Camera scan behavior on HTTPS production.

## 15. Risk Register

| Risk ID | Area | Risk | Severity | Evidence | Suggested Stabilization |
| --- | --- | --- | --- | --- | --- |
| R1 | Baseline | V1 stabilization is not committed yet, so V2 work could mix with V1 cleanup. | Medium | Dirty `git status` from V1 work | Preserve or commit V1 baseline before V2 feature changes |
| R2 | Reports | Inclusion rules for inactive products and non-active batches may be unclear. | Medium | Report queries aggregate all related stock batches | Document report business rules and add tests if rules change |
| R3 | Expiry | Expiry is not automatically processed by a scheduler. | Medium | Manual `mark_batch_expired()` and calculated status | Decide whether manual expiry is sufficient for V2 |
| R4 | Mobile scanner | iPhone camera scanning needs HTTPS. | Medium | Scanner JS secure-context check | Test production HTTPS camera flow and keep manual fallback |
| R5 | Operations | Backup commands exist, but restore should be rehearsed. | Medium | Backup docs/scripts present | Add a restore checklist and test on non-production data |
| R6 | Roadmap | V2 feature scope is not owner-approved yet. | Medium | V1 explicitly excludes many feature families | Gate new features behind owner decisions |

## 16. V2 Stabilization Recommendations

Recommended before feature work:

- Preserve the current V1 stabilization/no-internal-Nginx baseline.
- Convert this audit into stable docs and keep V2 decisions separate from implementation.
- Add or confirm manual mobile checks for iPhone LAN and HTTPS camera scanner.
- Rehearse backup/restore on non-production data.
- Use active products and active, non-expired, sellable stock for stock and low-stock reports.
- Use the explicit `expire_batches` maintenance command for expired available stock; no scheduler dependency is added during stabilization.
- Do not add new apps, dependencies, schemas, or public APIs until owner decisions are recorded.

## 17. Proposed V2 Phase Plan

Phase 0A: Baseline audit

- Goal: inspect and report current truth without changing files.
- Files affected: none.
- No-code/code: no-code.
- Reason: protect the V1 baseline.

Phase 0B: Documentation baseline

- Goal: create V2 audit, roadmap, business rules, testing checklist, and deployment runbook docs.
- Files affected: docs only.
- No-code/code: no-code.
- Reason: create shared implementation memory.

Phase 1: Existing V1 stabilization

- Goal: fix only proven V1 gaps.
- Files likely affected: targeted app code/tests/docs only if audit-backed.
- Reason: make V1 durable before V2 features.
- Requires user decision: report inclusion rules, automatic expiry policy, backup/restore expectations.

Phase 2: V2 feature discovery

- Goal: prioritize owner-approved V2 features.
- Files likely affected: roadmap/backlog docs first.
- Reason: avoid speculative feature work.
- Requires user decision: customer accounts, promotions, multi-branch, payments, mobile app, external integrations, exports.

## 18. Files Recommended for Documentation

Created in Phase 0B:

- `docs/legacy/V2_BASELINE_AUDIT.md`
- `docs/legacy/V2_ROADMAP.md`
- `docs/reference/BUSINESS_RULES.md`
- `docs/operations/TESTING_CHECKLIST.md`
- `docs/operations/DEPLOYMENT_RUNBOOK.md`

## 19. Final Recommendation

The system is ready for V2 audit and stabilization planning. It is not yet ready for new V2 business feature development.

Do first:

- Preserve the V1 baseline.
- Keep the V2 audit/docs as the source of truth.
- Decide the few open stabilization policies before coding.

Do not touch yet:

- New schemas for customers, branches, promotions, payments, or integrations.
- New dependencies or asynchronous infrastructure.
- Public APIs beyond the existing dashboard and scanner resolver.

Stabilization defaults chosen:

- Reports count active products and active, non-expired, sellable stock.
- Expiry is manual or explicit-command based through `expire_batches`.
- Restore rehearsal is monthly on a non-production copy.
- First V2 feature family is report exports.
