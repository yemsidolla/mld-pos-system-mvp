# V5 Product & UX Audit — Melodu POS & Inventory Control System

Read-only audit conducted by inspecting the codebase at `main` (post-V4, plus
the V5 sidebar regrouping). Scope: 10 Django apps, 13 models, 49 URL routes, 40
templates. Every finding traces to a file — no functionality is assumed. This
document is an audit deliverable; it does not change code.

Status: **Approved** (2026-06-10). Owner decisions locked in
`docs/V5_PHASE_PLAN.md`.

---

## 1. Repository Overview

| App | Purpose | Key Models | Key Views | Key Templates |
| --- | --- | --- | --- | --- |
| **core** | Dashboard shell, auth, store settings, health, scan resolver, error pages, permission engine, data-reset command | `StoreSetting` (singleton) | `dashboard_home_view`, `dashboard_login_view`, `store_settings_view`, `scan_resolve_view`, `health_check` | `dashboard/base.html`, `home.html`, `login.html`, `error.html`, `core/store_settings.html` |
| **accounts** | V4 role assignment + dashboard user management | `StaffProfile` | `user_list_view`, `user_create_view`, `user_edit_view` | `accounts/user_list.html`, `user_form.html` |
| **catalog** | Product master data + classification + suppliers + reference costs | `Product`, `Category`, `Brand`, `Supplier`, `SupplierProductCost`, `ProductTag` | `product_*`, `category_*`, `brand_*`, `supplier_*`, `supplier_product_cost_*`, `catalog_quick_create_view` | `catalog/product_list.html`, `product_form.html`, `master_data_list.html`, `master_data_form.html`, `supplier_product_cost_*` |
| **inventory** | Stock-in (batches), inventory summary, adjustments/damage/expiry, barcode/QR print | `StockBatch`, `InventoryMovement` | `stock_in_view`, `inventory_summary_view`, `stock_batch_detail_view`, `barcode_print_view` | `inventory/stock_in.html`, `inventory_summary.html`, `stock_batch_detail.html`, `barcode_print.html` |
| **labels** | V4 label template system + product/promotion label printing | `LabelTemplate` | `label_template_*`, `label_print_view`, `promotion_label_print_view` | `labels/template_list.html`, `template_form.html`, `label_print.html`, `promotion_label_print.html` |
| **pos** | Cart, checkout, receipt, sales history, cancellation, promotions | `Sale`, `SaleItem`, `Promotion` | `pos_sale_view`, `sale_receipt_view`, `sale_reprint_view`, `sales_history_view`, `sale_detail_view`, `sale_cancel_view`, `promotion_*` | `pos/pos_sale.html`, `receipt.html`, `sales_history.html`, `sale_detail.html`, `promotion_list.html`, `promotion_form.html` |
| **reports** | 6 operational reports | (none — reads other apps) | `reports_index_view` + 6 report views | `reports/index.html` + 6 report templates |
| **batch_upload** | CSV/XLSX import with preview/commit | `BatchUploadJob`, `BatchUploadRow` | `batch_upload_index/detail/commit/row_update/row_delete/template` | `batch_upload/index.html`, `detail.html` |
| **audit** | Immutable audit trail (28 action types) | `AuditLog` | (no dashboard view — Django Admin only) | (admin only) |
| **system_logs** | Live backend log viewer + system health | (none — reads log files) | `live_logs_view`, `system_health_view` | `system_logs/live_logs.html`, `system_health.html` |

**Management commands (4):** `setup_roles`, `set_user_role` (accounts);
`reset_business_data` (core); `expire_batches` (inventory).

**Permission engine** (`core/permissions.py`): role resolution
`superuser → Owner › StaffProfile.role › legacy Admin/Cashier group › None`,
plus capability functions and per-capability decorators (`admin_required`,
`pos_required`, `inventory_required`, `reports_required`,
`sales_history_required`, `system_required`, `settings_required`,
`users_required`).

---

## 2. Menu Map (actual, from `core/context_processors.py`)

```
Overview
└── Dashboard

Sales
├── POS
└── Sales History

Catalog
├── Products
├── Categories
├── Brands
├── Suppliers
├── Costs                  (page title says "Reference Costs")
├── Promotions
├── Label Templates
└── Batch Upload

Inventory
├── Stock-In
├── Inventory
├── Barcode / QR Print
├── Print Labels
└── Promotion Labels

Reports
└── Reports                (index → 6 sub-reports, not in sidebar)

Administration
├── Users
├── Settings
└── System                 (→ System Health)

Footer (pinned): Django Admin (admin/superuser only)

Hidden / not in sidebar:
• Audit Logs (Django Admin only)
• Data Reset (CLI only)
• Live Logs (no nav entry)
• 6 report sub-pages (only from Reports index)
• All create/edit screens (contextual)
• Inventory adjustments (batch detail sub-actions)
```

---

## 3. Screen Inventory

~48 user-facing dashboard screens + the Django Admin site + the standalone
print receipt page. Six list screens share the same create/edit pattern
(Products, Categories, Brands, Suppliers, Reference Costs, Promotions, Label
Templates) — a candidate for a shared "managed list" component.

---

## 4. Key Findings

### 4.1 High-impact (code-level) — Dashboard Home is role-blind

`dashboard_home_view` branches only on `is_admin_user` (Owner/Manager). For
**Inventory staff** and **Viewer** roles it renders the *cashier* branch —
showing "POS Ready: Yes", an "Open POS" button, and a "POS Sale" quick action —
but `can_access_pos` excludes Inventory and Viewer, so following those leads to
a **403 dead-end**. The Inventory/Reports shortcuts those roles *can* use are
hidden. Highest-ROI fix in V5.

### 4.2 Hidden functionality

- **Audit Logs** are recorded (28 action types) but viewable only in Django
  Admin — invisible to non-`is_staff` Owners/Managers.
- **Live Logs** has no sidebar entry (orphaned).
- **Data Reset** is CLI-only (intentional, but undocumented in-app).

### 4.3 Duplicate / fragmented workflows

- **Two label-print entry points**: legacy "Barcode / QR Print" (Phase 4) and
  template-driven "Print Labels" (V4) both print batch labels.
- **Receive → print label** requires re-selecting the same batch on a second
  screen (no shortcut from stock-in success or batch detail).
- **Label features split across groups**: Label Templates in Catalog; Print
  Labels / Promotion Labels / Barcode in Inventory.

### 4.4 UI consistency

- **No pagination anywhere** (zero `Paginator`/`page_obj` usage): every list
  renders all rows — a scalability and mobile-performance risk.
- **Three different "search" mechanisms**: server-side GET filter forms
  (Products, Sales History), client-side JS row filter (Inventory Summary),
  bespoke search fields (Reference Costs, Promotions).
- **Batch status badge** renders the raw enum (`SOLD_OUT`) with no color, unlike
  the colored product status badge; should use `get_status_display` + color.
- Buttons, alerts, empty states, page headers, and the color-token palette are
  otherwise consistent. No icon system (text-only nav/buttons).

### 4.5 Naming

| Current | Recommended | Reason |
| --- | --- | --- |
| Costs (sidebar) | Reference Costs | Matches page title; disambiguates from cost-price/batch-cost. |
| Stock-In | Receive Stock | Home already says "Receive Stock"; reduce jargon. |
| System (sidebar) | System Health | Item only opens System Health; "System" hides Live Logs. |
| Inventory (item) | Stock Overview | Item shares the exact word with its own group. |
| Custom Code | Shelf/Batch Code | Internal terminology shown to staff. |
| Barcode / QR Print | (consolidate or "Quick Barcode") | Two near-identical label entries in one group. |

### 4.6 Mobile / tablet

- Responsive shell is solid (sidebar → bottom nav at 900px; form stacking at
  640px; POS single-column with non-sticky cart).
- **Bottom nav** shows the first 5 flattened items, text-only, no icons — for
  admins the slots aren't the highest-value destinations.
- **Wide tables** (Sales History, Inventory batches, Stock Movement) rely on
  horizontal scroll with no stacked/card fallback.

---

## 5. Prioritized Backlog (see V5_PHASE_PLAN.md for sequencing)

**Quick wins:** role-aware home; clarity renames; colored batch status badge;
stock-in→print shortcut; Live Logs nav entry.

**Medium:** read-only Audit Log dashboard page; unify search; consolidate label
print entry points; add pagination; shared CRUD list/form component.

**Major (future):** mobile table strategy; icon set + smarter bottom nav;
cost-terminology rationalization; unified "Labels" hub.
