# V2 Phase 2B: Dashboard Access And POS UX Stabilization

Date: 2026-06-09

## Summary

Phase 2B adds a staff-friendly dashboard authentication flow, clearer role-denial behavior, friendly error pages, safer missing-object handling, and small POS usability improvements. This phase does not change sale calculation, stock deduction, schema, dependencies, or Docker deployment shape.

## What Changed

- Added `/dashboard/login/` and `/dashboard/logout/`.
- Set dashboard auth redirects to the dashboard login flow instead of Django Admin login.
- Added POST-only logout with a success message.
- Standardized dashboard role checks so anonymous users redirect to login and wrong-role users see 403.
- Added friendly 403, 404, and 500 pages.
- Hid the Django Admin link from non-admin dashboard users.
- Hardened invalid report dates and invalid batch-upload template targets.
- Improved POS scan/cart empty states, unavailable stock text, checkout button text, and double-submit protection.

## What Did Not Change

- POS sale calculation was not changed.
- Stock deduction was not changed.
- Sale cancellation logic was not changed.
- Stock-in still uses the existing stock service.
- No migrations, dependencies, public registration, payment features, discount features, customer features, or advanced RBAC were added.
- Docker compose services remain `postgres` and `web`.

## Role Behavior

- Admin: full dashboard management access and POS access.
- Cashier: dashboard home, POS, scan resolver, and receipts.
- Unassigned: friendly 403 after login.
- Inactive: blocked at login; invalid inactive sessions are treated as unauthenticated by Django.
- Anonymous: redirected to `/dashboard/login/?next=...`.

## POS UX Behavior

- Empty POS state tells staff to scan or type a product code.
- Product lookup state tells staff to choose a stock batch and quantity.
- Empty cart state explains that a sellable batch is required before checkout.
- Checkout button reads `Complete Sale` and disables after submit.
- Successful checkout adds a friendly message before showing the receipt.

## Rollback

- Restore `LOGIN_URL` to the previous value if dashboard login must be disabled.
- Remove the dashboard login/logout routes and templates.
- Restore the previous role decorators if redirect-on-denial behavior is required.
- Keep the POS service layer unchanged; rollback does not require schema or data changes.
