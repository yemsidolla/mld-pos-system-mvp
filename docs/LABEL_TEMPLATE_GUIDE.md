# Label Template Guide (V4 Phase 4)

Flexible product/shelf/promotion labels using preset, configurable templates
(no drag-and-drop builder). Printing uses the browser print dialog.

## Who can do what

- **Manage templates** (create/edit): Owner, Manager — **Label Templates**
  (`/dashboard/labels/templates/`).
- **Print labels**: Owner, Manager, Inventory staff — **Print Labels**
  (`/dashboard/labels/print/`).

A default **Standard Product Label** (50×30mm) is created automatically.

## Label templates

Each `LabelTemplate` has:

- **Name** and **type**: Product, Shelf, Promotion, or Custom.
- **Paper width/height (mm)** and **orientation**; **font size (px)**.
- Field toggles: store name, logo, product name, price, SKU (product code),
  barcode, QR, batch number, expiry date, animal type, life stage.
- **Header text** and **custom footer**.
- **Default** (one default per type) and **Active** flags.

Templates are also editable in Django Admin under **Label template**.

## Printing

1. Open **Print Labels**.
2. Choose a template, select one or more **active stock batches**, and set the
   **quantity** (copies per batch).
3. **Preview** to see the labels, then **Print** to open the browser print
   dialog. Printing records a `BARCODE_PRINT` audit entry with the template and
   batch numbers.

Labels read data from the selected stock batches (barcode/QR images, price,
expiry, batch number) and the product (name, SKU, animal type, life stage), plus
the store name/logo from Store Settings. Only the fields enabled on the template
are shown.

## Notes

- The legacy single-batch **Labels** page (`/dashboard/barcode-print/`) still
  exists for quick prints; the template-driven **Print Labels** page is the
  flexible option.
- Promotion labels (Phase 5) reuse this template system (Promotion type).
- For small label stock, set the printer paper size to match the template and
  margins to none in the browser print dialog.
