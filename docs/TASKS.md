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
| Create Nginx config | Done |
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
