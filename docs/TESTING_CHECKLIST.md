# Melodu POS Testing Checklist

Date: 2026-06-09

## Baseline Commands

Run from the repository root.

```bash
docker compose -f docker-compose.yml -f docker-compose.local.yml config --services
docker compose -f docker-compose.prod.yml config --services
docker compose -f docker-compose.yml -f docker-compose.local.yml exec web python manage.py check
docker compose -f docker-compose.yml -f docker-compose.local.yml exec web python manage.py test
docker compose -f docker-compose.yml -f docker-compose.local.yml exec web python manage.py collectstatic --noinput
docker compose -f docker-compose.yml -f docker-compose.local.yml restart web
docker compose -f docker-compose.yml -f docker-compose.local.yml exec -T -e DJANGO_SECRET_KEY=replace-with-64-character-secret-value-1234567890abcdef1234567890abcdef -e DJANGO_SESSION_COOKIE_SECURE=True -e DJANGO_CSRF_COOKIE_SECURE=True -e DJANGO_SECURE_SSL_REDIRECT=True -e DJANGO_SECURE_HSTS_SECONDS=31536000 -e DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS=True -e DJANGO_SECURE_HSTS_PRELOAD=True web python manage.py check --deploy
sh -n scripts/backup_db.sh scripts/backup_media.sh scripts/restore_db.sh scripts/restore_media.sh
```

Expected compose services:

```text
postgres
web
```

Expected health checks:

```bash
curl http://127.0.0.1:8000/health/
curl -I http://192.168.1.199:8000/health/
```

## Preflight

- Confirm the local Docker stack is healthy.
- Confirm `/health/` returns database `ok`.
- Confirm local dashboard opens at `http://127.0.0.1:8000/dashboard/`.
- Confirm iPhone on same Wi-Fi can open `http://192.168.1.199:8000/dashboard/`.
- Confirm login works with the local development admin account.

## Role And Permission Tests

- Anonymous dashboard access redirects to `/dashboard/login/`.
- Login redirects to a safe `next` URL or `/dashboard/`.
- Unsafe external `next` URLs are ignored.
- Logout is POST-only and returns to `/dashboard/login/`.
- Inactive users cannot log in.
- Admin can open dashboard home.
- Admin can open products, categories, brands, suppliers, stock-in, inventory, batch upload, labels, sales, reports, system health, and live logs.
- Admin can open reference costs and promotions.
- Cashier can open POS.
- Cashier can open receipts.
- Cashier cannot open inventory, sales history, reports, batch upload, system health, live logs, or Django Admin.
- Cashier and unassigned users see the friendly access-denied page for blocked dashboard pages.

## Error Page Tests

- 403 page shows access denied without internal details.
- 404 page shows page/item not found without internal details.
- 500 page shows unexpected error without internal details.
- Missing product, sale, stock batch, batch upload job, and invalid template URLs do not expose tracebacks.
- Invalid daily sales report date falls back with a friendly message.

## Catalog Tests

- Create and edit category.
- Create and edit brand.
- Create and edit supplier.
- Quick-create category from the Product form modal.
- Quick-create brand from the Product form modal.
- Reject duplicate quick-created category/brand/supplier names.
- Confirm quick-create actions write audit logs.
- Create and edit product.
- Search product by name, product code, and original barcode.
- Filter products by category, brand, and status.
- Confirm create/update actions write audit logs.
- Create and edit supplier/product reference cost.
- Reject duplicate supplier/product reference cost rows.
- Confirm reference cost changes write `COST_CHANGE` audit logs.

## Stock-In And Inventory Tests

- Receive stock for active product and active supplier.
- Confirm actual unit cost is stored on the stock batch.
- Confirm landed unit cost is optional and stored when provided.
- Quick-create supplier from the Stock-In form modal.
- Reject stock-in for inactive product.
- Reject stock-in for inactive supplier.
- Reject zero or negative stock-in quantity.
- Reject product without original barcode.
- Confirm batch number and custom code are generated.
- Confirm barcode and QR images are generated.
- Confirm `STOCK_IN` movement and audit log are created.
- Confirm `STOCK_BATCH_COST_CHANGE` audit log is created.
- Adjust stock up and down.
- Reject adjustment without reason.
- Reject adjustment that makes stock negative.
- Mark damaged stock.
- Mark expired stock.
- Run expired-batch maintenance dry run.
- Run expired-batch maintenance and confirm it uses the expiry workflow.
- Confirm movements and audit logs for each stock operation.

## POS Tests

- Scan original barcode and show available batches.
- Scan custom code and add exact batch to cart.
- Confirm POS empty state is clear before scan.
- Confirm lookup state is clear after scan.
- Add selected batch to cart.
- Update cart quantity.
- Remove cart item.
- Clear cart.
- Reject invalid quantity.
- Reject insufficient stock.
- Reject expired stock.
- Confirm sale.
- Confirm SaleItem snapshots cost basis, actual cost, landed cost, original price, final price, and discount.
- Confirm cashier below-cost sale is blocked with manager-approval message.
- Confirm admin below-cost override requires a reason.
- Confirm admin below-cost override writes audit logs.
- Confirm promotion is applied automatically when active.
- Confirm promotion does not stack and the best valid promotion wins.
- Confirm below-cost promotion is blocked unless `allow_below_cost` is enabled.
- Confirm below-cost promotion sale writes audit logs.
- Confirm cashier receipt/POS does not reveal cost or margin.
- Confirm checkout button disables after submit.
- Confirm sale success message appears before receipt.
- Confirm batch quantity is deducted.
- Confirm sold-out batch status changes.
- Confirm sale movement and audit log are created.
- Open receipt.

## Sale Cancellation Tests

- Admin opens sales history.
- Filter sales by date, cashier, and payment method.
- Open sale detail.
- Cancel completed sale with reason.
- Reject cancellation without reason.
- Reject cancellation for non-completed sale.
- Confirm original batch quantity is restored.
- Confirm `RETURN` movement and `SALE_CANCEL` audit log are created.

## Batch Upload Tests

- Upload CSV for each supported target.
- Upload XLSX for each supported target.
- Reject unsupported extension.
- Reject missing headers.
- Preview valid and invalid rows.
- Edit preview row.
- Delete preview row.
- Commit valid selected rows.
- Confirm invalid rows are not committed.
- Confirm stock-in upload uses normal stock-in business rules.
- Confirm stock-in upload accepts optional `landed_unit_cost`.
- Confirm audit summary is created after commit.

## Scanner Tests

- Open scanner modal from POS.
- Use manual code entry.
- Use image upload decode.
- Use camera scanner on HTTPS production or localhost.
- Confirm scanner resolver handles product code, original barcode, batch number, and custom code.
- Confirm resolver warnings appear for inactive, expired, unavailable, or zero-stock batches.

## Reports Tests

- Daily sales report shows completed totals.
- Stock summary report shows product stock totals.
- Low stock report uses `min_stock`.
- Stock and low-stock reports count only active sellable stock.
- Expiry report shows active available batches within 60 days.
- Stock movement report shows recent movements.
- Staff sales report groups completed sales by cashier.

## Deployment Tests

- `collectstatic` succeeds.
- Docker local stack exposes `0.0.0.0:8000`.
- Production compose binds web to localhost for host Nginx.
- No Docker Nginx service appears in compose config.
- Host Nginx proxy points to the configured Django/Gunicorn port.
- Static files load through WhiteNoise.
- Restart `web` after `collectstatic` so pages use the latest static manifest.
- Media files remain available after container restart.
- Database, media, static, and logs persist.

## Backup And Restore Tests

- Run database backup script.
- Run media backup script.
- Confirm database restore refuses to run without `CONFIRM_RESTORE=yes`.
- Confirm media restore refuses to run without `CONFIRM_RESTORE=yes`.
- Confirm backup files are created.
- Restore database backup on a non-production copy.
- Restore media backup on a non-production copy.
- Confirm dashboard and health check after restore.
