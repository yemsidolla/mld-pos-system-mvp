# Melodu Dashboard UX Guide

The Melodu Dashboard is the daily-work interface at `/dashboard/`.

Django Admin remains available at `/admin/` for raw model inspection, user/group management, and emergency maintenance.

Dashboard staff login is available at `/dashboard/login/`. Dashboard logout is POST-only at `/dashboard/logout/`.

## Design Direction

- Merchant admin structure inspired by Shopify Admin and Polaris.
- Fast retail scan workflow inspired by Square and Shopify POS.
- Dense, calm, operational screens rather than marketing-style pages.
- Shared layout, navigation, buttons, cards, tables, forms, alerts, badges, and modals.

## Role Behavior

- Admin users can access POS, stock-in, inventory, batch upload, label printing, sales, reports, system health, live logs, and Django Admin.
- Admin users can manage products at `/dashboard/products/` for daily catalog updates.
- Cashier users can access POS and cashier dashboard links only.
- Blocked authenticated users see a friendly access-denied page instead of a raw redirect or traceback.
- Business rules still live in Python services; the dashboard does not bypass them.

## Scanner

The scanner modal supports:

- Camera scanning
- Uploaded image decoding
- Manual code entry

Scanner buttons appear on:

- POS sale scan field
- Stock-in product lookup
- Barcode/QR print batch lookup
- Inventory search
- Batch upload preview code/barcode fields

The scanner only decodes and fills fields. It does not save photos and does not mutate sales, stock, upload jobs, inventory movements, or audit logs.

## Scan Resolver API

Endpoint:

```text
/dashboard/api/scan/resolve/
```

Query parameters:

- `value`: scanned or typed code
- `context`: optional workflow name such as `pos`, `stock_in`, `inventory`, `barcode_print`, or `batch_upload`

Supported values:

- Product code
- Original barcode
- Stock batch number
- Melodu custom code

The endpoint returns read-only product and stock batch metadata.

## Language

The dashboard supports English and Khmer with Django i18n.

The language selector is in the dashboard top action area.

## Production Camera Requirement

Camera scanning works on `localhost` for development.

On phones, tablets, and production domains, browser camera access requires HTTPS.
