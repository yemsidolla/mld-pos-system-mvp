# Promotion Label Guide (V4 Phase 5)

Print physical "special offer" labels for the products in a promotion. Built on
the Phase 4 label template system and the existing promotions.

## Who can print

Owner, Manager, Inventory staff — **Promotion Labels**
(`/dashboard/labels/promotions/`).

A default **Standard Promotion Label** (70×50mm) is created automatically.

## How it works

1. Open **Promotion Labels**.
2. Choose an active **promotion**, a **Promotion/Custom label template**, a
   **quantity** (copies per product), and optional **custom text**
   (default "Special Offer").
3. **Preview**, then **Print**.

The page resolves the promotion's products:

- Product-scoped promotion → that product (if active).
- Category-scoped promotion → all active products in the category.

For each product it computes the promotion price from the product's normal
selling price using the same pricing logic as the POS
(`calculate_promotion_price`), so labels always match what the till charges.

Each label shows the store name, the offer text, the product name, the **old
price** (struck through), the **new price**, the **savings**, and the promotion
period. Printing records a `BARCODE_PRINT` audit entry referencing the
promotion, template, and product codes.

## Notes

- Promotions are created and managed by Owner/Manager under **Promotions**; this
  page only prints labels for them.
- Use a Promotion-type label template sized for your shelf tags. Adjust paper
  size and font on the template, and printer paper/margins in the browser print
  dialog.
