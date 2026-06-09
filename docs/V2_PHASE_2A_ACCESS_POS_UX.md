# V2 Phase 2A: Dashboard Access And POS UX Stabilization

Date: 2026-06-09

## Current Slice: Inline Master-Data Quick Add

This slice adds at-spot creation for Category, Brand, and Supplier while preserving the Django monolith, existing dashboard pages, and all core stock/POS business logic.

## What Changed

- Product create/edit pages include inline quick-add buttons for Category and Brand.
- Stock-In includes an inline quick-add button for Supplier.
- A shared dashboard modal posts to `/dashboard/api/catalog/quick-create/`.
- Successful quick-create appends the new option to the related select and selects it immediately.
- Quick-created records are active by default.
- Each successful quick-create creates a catalog audit log.

## What Did Not Change

- Product creation remains the normal product creation workflow.
- Existing Category, Brand, and Supplier full CRUD pages remain available.
- POS sale calculation was not changed.
- Stock deduction was not changed.
- Stock-in still uses the existing `receive_stock()` service.
- No dependencies, migrations, new apps, or public registration were added.

## Access Rules

- Admin users can quick-create Category, Brand, and Supplier.
- Cashier users cannot quick-create master data.
- Anonymous users are redirected to login by Django auth.
- Unassigned or inactive users are not allowed by the Admin role check.

## Validation Rules

- `type` must be one of `category`, `brand`, or `supplier`.
- Name is required.
- Exact or case-insensitive duplicate names are rejected with a friendly validation error.
- Category and Brand accept optional description.
- Supplier accepts optional contact person, phone, and Telegram.

## UX Behavior

- The modal opens without leaving the current page.
- Existing unsaved form data remains in place.
- Failed validation stays in the modal with inline error text.
- Escape, backdrop, close, and cancel close the modal.
- Focus returns to the button that opened the modal.

## Test Notes

Coverage includes:

- Admin quick-create success for Category, Brand, and Supplier.
- Duplicate-name rejection.
- Unsupported-type rejection.
- Cashier denial.
- Anonymous redirect.
- Product form quick-add controls.
- Stock-In supplier quick-add control.

## Rollback

- Remove the quick-create route and modal include.
- Remove `data-quick-create` buttons from Product and Stock-In templates.
- Keep existing full CRUD pages; they are unchanged and remain the fallback.

