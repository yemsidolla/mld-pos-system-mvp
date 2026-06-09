# Melodu POS Business Rules

Date: 2026-06-09

## Core Rule

All sellable stock is controlled at stock batch level.

```text
Product is master data.
StockBatch is sellable stock.
SaleItem must always link to StockBatch.
Stock deduction must always happen from StockBatch.quantity_available.
Every stock change must create InventoryMovement.
Every important business action must create AuditLog.
```

## Catalog Rules

- Category, Brand, and Supplier names are unique.
- Product `product_code` is unique.
- Product `original_barcode` is optional, but unique when present.
- Products, categories, brands, and suppliers can be marked inactive.
- Product category and brand are optional.
- Product price fields use decimals.

Evidence:

- `catalog.models`
- `catalog.forms`
- `catalog.views`
- `batch_upload.services`

## Stock-In Rules

- Stock-in requires an active product.
- Stock-in requires an active supplier.
- Quantity must be greater than zero.
- Expiry date is required.
- Stock batch actual unit cost is recorded at receiving time.
- Stock batch landed unit cost is optional and records actual cost plus shipping, import, or extra costs.
- Product must have an original barcode before stock-in.
- Batch number format is `BYYNNNN`.
- Custom code format is `[original_barcode]-M-[expiry_yymmdd]-[batch_no]`.
- Stock-in creates barcode and QR image files.
- Stock-in creates one `InventoryMovement` with type `STOCK_IN`.
- Stock-in creates one audit log with action `STOCK_IN`.
- Stock-in creates one audit log with action `STOCK_BATCH_COST_CHANGE`.

Evidence:

- `inventory.services.receive_stock()`
- `inventory.services.generate_batch_number()`
- `inventory.services.build_custom_code()`

## Stock Batch Rules

- `quantity_available` cannot be negative.
- `quantity_received` must be positive.
- `quantity_available` cannot exceed `quantity_received`.
- Batches can be Active, Sold out, Expired, Damaged, or Locked.
- Expiry status labels are Expired, Critical, Warning, and Normal.
- Expired-batch maintenance must use the same expiry service as manual expiry so movements and audit logs are created.

Evidence:

- `inventory.models.StockBatch`
- `inventory.services.get_expiry_status()`
- `inventory.management.commands.expire_batches`

## POS Sale Rules

- POS access is allowed for Admin and Cashier users.
- Empty carts cannot be confirmed.
- Sale quantity must be greater than zero.
- Inactive products cannot be sold.
- Non-active batches cannot be sold.
- Expired batches cannot be sold.
- Insufficient stock cannot be sold.
- Original barcode scan returns product and available batches.
- Custom code scan selects the exact stock batch.
- Sale confirmation runs transactionally.
- Sale confirmation creates `Sale`, `SaleItem`, `InventoryMovement SALE`, and `AuditLog SALE_CREATE`.
- Sold-out batches are marked `SOLD_OUT`.
- Discount cannot be negative or exceed the sale total.
- Sale validation uses cost basis in this order: landed unit cost, actual unit cost, supplier/product reference cost, then product default cost.
- Cashier users cannot confirm below-cost sales.
- Admin users can confirm below-cost sales only with an override reason.
- Promotions can produce below-cost sales only when `allow_below_cost` is enabled.
- SaleItem snapshots preserve reference cost, actual cost, landed cost, cost basis, original price, final price, discount, promotion, and override details.

Evidence:

- `pos.views.pos_sale_view()`
- `pos.services.scan_code()`
- `pos.services.validate_sellable_batch()`
- `pos.services.confirm_sale()`

## Supplier Reference Cost Rules

- Supplier/product reference cost stores the expected cost for one supplier and one product.
- Only one reference cost row can exist per supplier/product pair.
- Reference costs are Admin-only dashboard records.
- Creating or editing a reference cost creates `AuditLog.Action.COST_CHANGE`.

Evidence:

- `catalog.models.SupplierProductCost`
- `catalog.views.supplier_product_cost_list_view()`

## Promotion Rules

- Only Admin users can create or edit promotions.
- Promotions can apply to a product or a category.
- Supported discount types are percentage, fixed amount, and fixed final price.
- Active date range is required.
- Promotions do not stack.
- If multiple promotions apply, the lowest final unit price wins.
- Promotion create/update/deactivation creates promotion audit logs.
- Below-cost promotion sales create `PROMOTION_BELOW_COST_SALE` audit logs.

Evidence:

- `pos.models.Promotion`
- `pos.pricing.choose_best_promotion()`
- `pos.services.confirm_sale()`

## Sale Cancellation Rules

- Only Admin users can access sale history/detail/cancellation.
- Only completed sales can be cancelled.
- Cancellation requires a reason.
- Cancellation restores quantity to each original stock batch.
- Restored expired batches are marked `EXPIRED`.
- Cancellation creates `InventoryMovement RETURN`.
- Cancellation creates `AuditLog SALE_CANCEL`.

Evidence:

- `pos.views.sale_cancel_view()`
- `pos.services.cancel_sale()`

## Inventory Adjustment Rules

- Adjustment requires a reason.
- Adjustment delta cannot be zero.
- Adjustment cannot make stock negative.
- Damage flow requires a reason and positive quantity.
- Damage cannot make stock negative.
- Expiry flow requires a reason.
- Expiry flow only applies when available quantity is greater than zero.
- Adjustment, damage, and expiry flows create inventory movements and audit logs.

Evidence:

- `inventory.services.adjust_stock()`
- `inventory.services.mark_batch_damaged()`
- `inventory.services.mark_batch_expired()`

## Batch Upload Rules

- Supported targets: categories, brands, suppliers, products, stock-in.
- Supported file types: CSV and XLSX.
- Headers must match the target schema.
- Upload creates preview jobs and rows.
- Rows can be edited or deleted before commit.
- Rows are revalidated before commit.
- Invalid selected rows are marked failed, not committed.
- Deleted or unselected rows are skipped.
- Category, Brand, and Supplier upload uses `name` as update-or-create key.
- Product upload uses `product_code` as update-or-create key.
- Product upload validates category and brand names when provided.
- Product upload validates barcode uniqueness.
- Stock-in upload uses the normal `receive_stock()` service.
- Commit creates an audit summary.

Evidence:

- `batch_upload.models`
- `batch_upload.services`
- `batch_upload.views`

## Scanner Rules

- Scanner modal supports camera, image upload, and manual entry.
- Camera scanning requires secure context; localhost is allowed for development.
- Resolver endpoint is read-only.
- Resolver can match custom code, batch number, product code, and original barcode.
- Resolver returns warnings for inactive product, non-active batch, zero quantity, and expired batch.

Evidence:

- `core.static.core.js.scanner.js`
- `core.views.scan_resolve_view()`

## Permission Rules

- Superuser and Admin group members can access management pages.
- Cashier group members can access POS and receipts.
- Cashier-only users are blocked from Django Admin.
- Dashboard navigation is role-aware.

Evidence:

- `core.permissions`
- `core.middleware.CashierAdminBlockMiddleware`
- `core.context_processors.dashboard_context`

## Open Business Decisions For V2

- Reports use active products and active, non-expired, sellable stock by default.
- Expiry is handled manually or by the explicit `expire_batches` maintenance command; no scheduler dependency is added in V2 stabilization.
- Restore rehearsal frequency is monthly on a non-production copy.
- Should receipts/report exports require PDF or CSV support?
- Which V2 feature family comes first after stabilization?
