# Label Template Guide (V4 Phase 4)

Flexible product/shelf/promotion labels using preset, configurable templates
(no drag-and-drop builder). Printing uses the browser print dialog.

## Who can do what

- **Manage templates** (create/edit): Owner, Manager — **Label Templates**
  (`/dashboard/labels/templates/`).
- **Print labels**: Owner, Manager, Inventory staff — **Print Labels**
  (`/dashboard/labels/print/`).

A default **Standard Product Label** (50×30mm) is created automatically.

## Managing templates

The dashboard list shows the number of templates, defaults, and inactive
templates. Each row shows type, size, orientation, font size, field toggles,
default status, active status, and edit action.

The template form is grouped into:

- **Template Identity**
- **Paper And Text**
- **Fields On Label**
- **Custom Text**
- **Default And Status**

Marking one template as default only unsets the previous default for the same
template type. It does not delete or overwrite other templates.

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
3. **Preview** to review template type, selected batch count, copies per batch,
   total labels, and the rendered label output.
4. **Print** to open the browser print
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
- Promotion label preview shows the promotion, active product count, copies per
  product, total labels, and promotion window before opening print.
- For small label stock, set the printer paper size to match the template and
  margins to none in the browser print dialog.
- Test new default templates on the physical printer before staff use them for
  live shelf or product labeling.
