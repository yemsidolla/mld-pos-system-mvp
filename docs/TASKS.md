# Melodu POS Task Tracker

Statuses: Pending, AI Planned, AI Generated, Human Reviewing, Fix Required, Testing, Done.

## Phase 0: Project Bootstrap

| Task | Status |
| --- | --- |
| Create repository structure | Done |
| Create Django project | Done |
| Create Django apps | Done |
| Create Dockerfile | Done |
| Create docker-compose.yml | Done |
| Document external host Nginx config | Done |
| Configure PostgreSQL | Done |
| Configure environment variables | Done |
| Configure static/media/log folders | Done |
| Add health check endpoint | Done |
| Add README setup commands | Done |
| Create first superuser instruction | Done |
| Verify docker compose startup | Done |
| Verify Django admin opens | Done |
| Verify PostgreSQL connection | Done |
| Verify health check endpoint | Done |
| Verify persistence after restart | Done |

## Phase 1: Master Data

| Task | Status |
| --- | --- |
| Create Category model | Done |
| Create Brand model | Done |
| Create Supplier model | Done |
| Create Product model | Done |
| Register models in Django Admin | Done |
| Add dashboard product management page | Done |
| Add admin search and filters | Done |
| Add original barcode field | Done |
| Add product active/inactive status | Done |
| Add basic tests | Done |

## Phase 2: Audit Foundation

| Task | Status |
| --- | --- |
| Create AuditLog model | Done |
| Create audit helper function | Done |
| Capture user, IP, user agent | Done |
| Register AuditLog in read-only admin | Done |
| Log login success | Done |
| Log login failed | Done |
| Add audit helper tests | Done |

## Phase 3: Stock-In and Batch

| Task | Status |
| --- | --- |
| Create StockBatch model | Done |
| Create InventoryMovement model | Done |
| Generate batch number | Done |
| Generate custom code | Done |
| Generate barcode image | Done |
| Generate QR image | Done |
| Create stock-in workflow | Done |
| Create inventory movement for stock-in | Done |
| Create audit log for stock-in | Done |
| Add tests | Done |

## Phase 4: Barcode / QR Print

| Task | Status |
| --- | --- |
| Create label preview page | Done |
| Select stock batch | Done |
| Generate printable label | Done |
| Support multiple label quantity | Done |
| Record barcode print audit log | Done |

## Phase 5: POS Sale

| Task | Status |
| --- | --- |
| Create POS page | Done |
| Create scan input | Done |
| Support original barcode lookup | Done |
| Support custom code lookup | Done |
| Show batch selection for original barcode | Done |
| Add item to cart | Done |
| Create Sale model | Done |
| Create SaleItem model | Done |
| Confirm sale transactionally | Done |
| Deduct stock batch | Done |
| Create inventory movement | Done |
| Create audit log | Done |
| Show receipt | Done |
| Add tests | Done |

## Phase 6: Sales History and Cancellation

| Task | Status |
| --- | --- |
| Create sales history page | Done |
| Add filters | Done |
| View sale detail | Done |
| Cancel sale with reason | Done |
| Reverse stock to original batch | Done |
| Create reversal inventory movement | Done |
| Create cancellation audit log | Done |

## Phase 7: Inventory Adjustment and Expiry Control

| Task | Status |
| --- | --- |
| Create inventory page | Done |
| Show product stock summary | Done |
| Show batch stock detail | Done |
| Add inventory adjustment flow | Done |
| Require adjustment reason | Done |
| Prevent negative stock | Done |
| Mark damaged stock | Done |
| Mark expired stock | Done |
| Show expiry warning status | Done |
| Add audit log | Done |
| Add inventory movement | Done |
| Add tests | Done |

## Phase 8: Reports

| Task | Status |
| --- | --- |
| Daily sales report | Done |
| Stock summary report | Done |
| Low stock report | Done |
| Expiry report | Done |
| Stock movement report | Done |
| Staff sales report | Done |

## Phase 9: Live Backend Logs and System Health

| Task | Status |
| --- | --- |
| Configure Python logging | Done |
| Create log files | Done |
| Create live log viewer page | Done |
| Auto-refresh logs | Done |
| Create system health page | Done |
| Check database status | Done |
| Check log writable status | Done |
| Check disk space | Done |
| Show last error | Done |
| Restrict access to Admin | Done |

## Phase 10: Permission and Security

| Task | Status |
| --- | --- |
| Create Admin role | Done |
| Create Cashier role | Done |
| Restrict cashier to POS only | Done |
| Restrict audit logs to Admin | Done |
| Restrict backend logs to Admin | Done |
| Protect dashboard pages with login | Done |
| Configure CSRF protection | Done |
| Configure secure cookie settings | Done |
| Add permission tests | Done |

## Phase 11: Production Deployment and Backup

Phase 0 created starter deployment files only. Final production deployment and backup hardening remains pending for Phase 11.

| Task | Status |
| --- | --- |
| Prepare production Docker Compose settings | Done |
| Prepare .env.example | Done |
| Add deployment guide | Done |
| Add backup guide | Done |
| Add database backup command | Done |
| Add media backup command | Done |
| Add restore instruction | Done |
| Add production checklist | Done |

## Batch Upload Feature

| Task | Status |
| --- | --- |
| Add XLSX parser dependency | Done |
| Create batch upload app | Done |
| Create upload job model | Done |
| Create upload row model | Done |
| Add CSV and XLSX parsing | Done |
| Add target schemas and templates | Done |
| Add category upload | Done |
| Add brand upload | Done |
| Add supplier upload | Done |
| Add product upload | Done |
| Add stock-in upload through receive_stock service | Done |
| Add preview validation | Done |
| Add row edit from preview | Done |
| Add row delete from preview | Done |
| Add commit workflow | Done |
| Add upload audit summary | Done |
| Restrict batch upload to Admin users | Done |
| Add batch upload tests | Done |
| Add batch upload documentation | Done |

## Melodu Dashboard UX/UI Upgrade

| Task | Status |
| --- | --- |
| Add shared dashboard shell | Done |
| Add desktop sidebar navigation | Done |
| Add mobile bottom navigation | Done |
| Add role-aware navigation | Done |
| Add dashboard home page | Done |
| Add shared CSS components | Done |
| Add reusable scanner modal | Done |
| Vendor scanner library locally | Done |
| Add image upload decode support | Done |
| Add manual scanner fallback | Done |
| Add scan resolver API | Done |
| Add POS scanner button | Done |
| Add stock-in scanner button | Done |
| Add barcode print scanner button | Done |
| Add inventory scanner lookup | Done |
| Add batch upload row scanner buttons | Done |
| Configure English and Khmer languages | Done |
| Convert POS page to dashboard shell | Done |
| Convert inventory pages to dashboard shell | Done |
| Convert batch upload pages to dashboard shell | Done |
| Convert sales pages to dashboard shell | Done |
| Convert reports pages to dashboard shell | Done |
| Convert system pages to dashboard shell | Done |
| Add dashboard and scanner tests | Done |
| Add dashboard UX documentation | Done |

## V2 Baseline And Stabilization

| Task | Status |
| --- | --- |
| Produce V2 baseline audit documentation | Done |
| Produce V2 roadmap documentation | Done |
| Produce business rules documentation | Done |
| Produce testing checklist documentation | Done |
| Produce deployment runbook documentation | Done |
| Produce V2 feature backlog | Done |
| Stabilize stock report inclusion rules | Done |
| Add audited expired-batch maintenance command | Done |
| Harden backup and restore scripts | Done |

## V2 Phase 2A: Inline Master-Data Quick Add

| Task | Status |
| --- | --- |
| Add inline category quick-create from product form | Done |
| Add inline brand quick-create from product form | Done |
| Add inline supplier quick-create from stock-in form | Done |
| Add admin-only quick-create JSON endpoint | Done |
| Add quick-create audit logging | Done |
| Add quick-create duplicate validation | Done |
| Add quick-create tests and documentation | Done |

## V2 Phase 2B: Dashboard Access And POS UX Stabilization

| Task | Status |
| --- | --- |
| Add dashboard login page | Done |
| Add POST-only dashboard logout | Done |
| Standardize Admin/Cashier/unassigned access behavior | Done |
| Add friendly 403/404/500 pages | Done |
| Hide Django Admin link from non-admin dashboard users | Done |
| Harden invalid report date and batch-upload template handling | Done |
| Improve POS empty states and checkout copy | Done |
| Add checkout double-submit protection | Done |
| Add Phase 2B tests and documentation | Done |

## V3 Phase 1: Cost Guardrails, Promotions, And Responsive POS

| Task | Status |
| --- | --- |
| Add supplier/product reference cost model and dashboard pages | Done |
| Add stock batch actual and landed unit costs | Done |
| Add SaleItem cost, price, promotion, and override snapshots | Done |
| Add cost-basis sale validation | Done |
| Block cashier below-cost sales | Done |
| Add admin below-cost override with required reason | Done |
| Add simple product/category promotions | Done |
| Add best-promotion selection without stacking | Done |
| Add below-cost promotion allowance flag | Done |
| Add V3 audit logging for cost, promotion, below-cost, and override events | Done |
| Add POS promotion labels, quantity steppers, sticky cart, and mobile layout improvements | Done |
| Add V3 tests and documentation | Done |

## V4 Phase 1: User Management & Permissions

| Task | Status |
| --- | --- |
| Add `accounts.StaffProfile` role model and migration | AI Generated |
| Backfill profiles for existing users (map and keep) | AI Generated |
| Rewrite `core.permissions` with roles, capabilities, and compatibility shims | AI Generated |
| Add dashboard user management (list/create/edit/disable) | AI Generated |
| Add role-aware navigation and Users link | AI Generated |
| Re-gate inventory, reports, and sales pages to the permission matrix | AI Generated |
| Extend `set_user_role`/`setup_roles` to five roles and profiles | AI Generated |
| Add Owner-only, self-protection, and last-Owner safeguards | AI Generated |
| Audit user create/update/role-change/disable | AI Generated |
| Add V4 Phase 1 tests and documentation | AI Generated |

## V4 Phase 2: Product Classification

| Task | Status |
| --- | --- |
| Add `catalog.ProductTag` model and migration | AI Generated |
| Add optional `animal_type` and `life_stage` fields to Product | AI Generated |
| Add tags/classification to product form | AI Generated |
| Add product list filters for animal type, life stage, and tag | AI Generated |
| Show classification in product list and Django Admin | AI Generated |
| Add optional batch-upload columns with backward compatibility | AI Generated |
| Auto-create tags and validate classification on upload | AI Generated |
| Include tag list in product audit snapshots | AI Generated |
| Add V4 Phase 2 tests and documentation | AI Generated |

## V4 Phase 3: Printer Settings & 80mm Receipt

| Task | Status |
| --- | --- |
| Add `core.StoreSetting` singleton model and migration | AI Generated |
| Add Owner/Manager store settings page with audit | AI Generated |
| Default receipt paper width to 80mm | AI Generated |
| Add standalone thermal receipt template driven by settings | AI Generated |
| De-hardcode store name on receipts and labels | AI Generated |
| Add audited reprint action and `RECEIPT_PRINT` audit type | AI Generated |
| Register StoreSetting in Django Admin as a singleton | AI Generated |
| Add Settings navigation link | AI Generated |
| Add V4 Phase 3 tests and documentation | AI Generated |

## V4 Phase 4: Label Template System

| Task | Status |
| --- | --- |
| Create `labels` app and register it | AI Generated |
| Add `LabelTemplate` model with field toggles and migration | AI Generated |
| Seed a default product template via data migration | AI Generated |
| Add Owner/Manager template management pages with audit | AI Generated |
| Add Owner/Manager/Inventory label print page with preview | AI Generated |
| Drive labels from a template + selected stock batches | AI Generated |
| Audit label printing | AI Generated |
| Add Label Templates and Print Labels navigation | AI Generated |
| Add V4 Phase 4 tests and documentation | AI Generated |

## V4 Phase 5: Promotion Label Printing

| Task | Status |
| --- | --- |
| Add promotion label print page (Owner/Manager/Inventory) | AI Generated |
| Resolve promotion products by product/category scope | AI Generated |
| Compute promo prices via shared pricing logic | AI Generated |
| Render old/new price, savings, and period labels | AI Generated |
| Seed a default promotion label template | AI Generated |
| Audit promotion label printing | AI Generated |
| Add Promotion Labels navigation | AI Generated |
| Add V4 Phase 5 tests and documentation | AI Generated |

## V4 Phase 6: Safe Data Reset / Admin Maintenance

| Task | Status |
| --- | --- |
| Add `reset_business_data` management command with scopes | AI Generated |
| Default to dry run; require --confirm to execute | AI Generated |
| Guard execution with ALLOW_DATA_RESET env flag | AI Generated |
| Require exact "RESET <scope>" phrase and backup acknowledgement | AI Generated |
| Run deletions in a single transaction in FK-safe order | AI Generated |
| Preserve users, settings, templates, and audit logs | AI Generated |
| Audit DATA_RESET before and after | AI Generated |
| Add V4 Phase 6 tests and runbook documentation | AI Generated |

## V5 Phase 1: Dashboard & Navigation Polish

| Task | Status |
| --- | --- |
| Make dashboard home capability-aware (no POS dead-end for Inventory/Viewer) | AI Generated |
| Apply staff-facing renames (Reference Costs, System Health, Receive Stock, Stock Overview) | AI Generated |
| Add Live Logs navigation entry under Administration | AI Generated |
| Color the batch status badge and use display labels in Stock Overview | AI Generated |
| Add role-aware home tests | AI Generated |

## V5 Phase 2: Audit Log Dashboard (read-only)

| Task | Status |
| --- | --- |
| Add `can_view_audit` capability and `audit_required` decorator | AI Generated |
| Add read-only audit log list view with filters and pagination | AI Generated |
| Add Audit Logs navigation entry under Administration | AI Generated |
| Add audit dashboard access and read-only tests | AI Generated |
