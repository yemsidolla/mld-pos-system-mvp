# Design System And UX Rules

Status: Implemented (documentation)
Last updated: 2026-06-17

**Authoritative design source:** `docs/DESIGN_SYSTEM.md` and `/dashboard/styleguide/`

This document summarizes how design rules apply to Melodu POS workflows. Do not edit
`docs/DESIGN_SYSTEM.md` or CSS tokens in normal feature work.

## Layout And Navigation

| Pattern | Rule | Status |
| --- | --- | --- |
| Dashboard shell | All business pages use shared dashboard layout | Implemented |
| Sidebar + mobile nav | Primary navigation; capability-aware items | Implemented |
| Page header | Title, subtitle, primary actions on the right | Implemented |
| Content width | Use dashboard content containers; avoid one-off page widths | Implemented |

Navigation groups (conceptual):

- Daily operations: POS, sales, stock receiving, inventory
- Catalog: products, categories, brands, suppliers, animal types
- Labels and printing: barcode print, label templates, promotion labels
- Management: promotions, batch upload, reports
- System: users, roles, settings, audit, logs, health

## Component Patterns

| Component | Rule | Status |
| --- | --- | --- |
| Tables | Use shared table classes; scroll wrapper on wide lists | Implemented |
| Forms | Shared form field, label, help, and error patterns | Implemented |
| Buttons | Primary / secondary / danger hierarchy | Implemented |
| Badges | Status colors from design tokens | Implemented |
| Empty states | Icon, title, explanation, next action | Partially Implemented |
| Alerts | Success, warning, error, info patterns | Implemented |
| Modals | Scanner modal is reusable; match modal pattern for new dialogs | Implemented |

## Button Consistency

| Type | Use for |
| --- | --- |
| Primary | Save, Complete Sale, Print, Receive Stock, Commit |
| Secondary | Cancel, Back, View details |
| Danger | Delete, Cancel Sale, Reset Data |

## Naming Rules

Use staff-friendly, consistent labels:

| Use | Avoid |
| --- | --- |
| Products | Catalog Item (mixed naming) |
| Receive Stock | Inconsistent Stock-In in user-facing text where avoidable |
| Promotion Labels | Promo Print |
| Stock Batch | Stock Lot (future staff-friendly alias — Needs Verification) |
| Sales History | Mixed sale list names |

Code route `/dashboard/stock-in/` may remain; user-facing label should prefer **Receive Stock**.

## Module UX Rules

### Cashier / POS

- POS screen is scan-first and keyboard-friendly
- Cart, payment, and confirm actions stay visible
- Receipt handoff after confirm to `/dashboard/pos/receipt/<id>/`
- Quick keys must submit real barcodes, not display-only text

### Inventory

- Stock receiving emphasizes product, supplier, quantity, expiry, cost, price
- Inventory summary highlights low stock and expiry risk
- Batch detail shows adjust/damage/expiry actions with reasons

### Reports

- Date filters and summary metrics above tables
- Cancelled sales must not count as completed revenue
- Table scroll on mobile

### Receipt And Label Print

- Browser print layouts; no ESC/POS driver dependency
- Print pages hide dashboard chrome (`no-print` classes)
- Label templates are configurable HTML/CSS, not drag-and-drop designer

## Access Denied And No-Role Behavior

| Case | Behavior | Status |
| --- | --- | --- |
| Unauthenticated | Redirect to login | Implemented |
| No recognised role | Access denied page | Implemented |
| Missing capability | 403 with audit for sensitive attempts | Implemented |
| Cashier | POS-focused nav; blocked from Django Admin | Implemented |

## Mobile And Tablet

| Rule | Status |
| --- | --- |
| Bottom mobile navigation on small screens | Implemented |
| Scanner modal works on HTTPS/localhost with camera permission | Partially Implemented |
| Phone camera/upload decode | Needs Verification on production devices |
| Tables scroll horizontally when needed | Partially Implemented |

## Khmer And English

| Rule | Status |
| --- | --- |
| Language switch in dashboard | Implemented |
| New UI strings should support translation hooks | Partially Implemented |
| Full Khmer coverage | Needs Verification |

## Design Change Process

Design-system changes require a dedicated task:

1. Update `docs/DESIGN_SYSTEM.md`
2. Update `/dashboard/styleguide/` if tokens/components change
3. Update shared CSS
4. Add/update tests if access or rendering changes
5. Manual browser check in final summary
