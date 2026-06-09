# Printer & Receipt Guide (V4 Phase 3)

Receipt printing uses the **browser print dialog** (File → Print or Ctrl/Cmd+P).
No special driver or app is required. Receipts default to **80mm** thermal width.
Direct Bluetooth/network ESC-POS printing is intentionally out of scope for now.

## Store & printer settings

Owner/Manager users open **Settings** in the sidebar (`/dashboard/settings/`):

- **Store name, address, phone, logo** — printed on receipts; the store name
  also appears on dashboard labels.
- **Receipt header / footer** — optional lines above/below the items.
- **Receipt paper width (mm)** — default **80**; allowed 40–120.
- **Receipt font size (px)** — default 12; allowed 8–24.
- **Show logo on receipt** — include the uploaded logo at the top.
- **Currency symbol** — prefix for amounts on the receipt (default `$`).

Settings are a single shared record. Every change is written to the audit log
(`SETTING_CHANGE`). The same values are also editable in Django Admin under
**Store setting** (single row, cannot be deleted).

## Printing a receipt

- After a sale, open the receipt from the POS success screen or sale detail and
  press **Print**. The receipt is a standalone page sized to the configured
  paper width, so the browser prints just the receipt (no dashboard chrome).
- For an 80mm thermal printer, set the printer's paper size to 80mm roll and
  margins to none in the browser print dialog.

## Reprinting

On a sale's detail page, Owner/Manager users see **Reprint Receipt**. This opens
the receipt and triggers the print dialog automatically, and records a
`RECEIPT_PRINT` audit entry for the sale. Cashiers can print the receipt for a
sale they just made but do not have the audited reprint action.

## Notes / future

- Browser print is the supported path in V4. If the store later needs direct
  thermal printing, that would be a separate, approved change.
- The receipt template is `app/templates/pos/receipt.html` (standalone, inline
  CSS, width driven by the configured paper size).
