# Dashboard Access Rules

Date: 2026-06-09

## Login And Logout

- Dashboard login URL: `/dashboard/login/`.
- Dashboard logout URL: `/dashboard/logout/`.
- Logout is POST-only and returns to `/dashboard/login/`.
- Successful login redirects to a safe `next` URL or `/dashboard/`.
- Already-authenticated users visiting `/dashboard/login/` are redirected to `/dashboard/`.
- Inactive users cannot log in through Django authentication.
- Django Admin keeps its own `/admin/login/` entry point.

## Roles

- Admin users can access dashboard management pages, reports, inventory, stock-in, batch upload, system health, live logs, sales history, and POS.
- Cashier users can access dashboard home, POS, scan resolver, and receipt pages.
- Cashier users cannot access catalog management, stock-in, inventory management, reports, sales management, batch upload, system health, live logs, or Django Admin.
- Authenticated users without Admin or Cashier role receive the dashboard access-denied page.
- Inactive users are blocked by Django authentication and treated as unauthenticated if their session is no longer valid.

## Error Handling

- Anonymous users are redirected to dashboard login.
- Authenticated active users with the wrong role receive a friendly 403 page.
- Missing dashboard records render a friendly 404 page.
- Unexpected server errors render a friendly 500 page without internal details.
- Dashboard-protected views use no-cache response headers as a best-effort back-button safeguard.

## Unchanged

- No public registration was added.
- No advanced RBAC or permission editor was added.
- Sale calculation and stock deduction logic were not changed.
- Docker still uses only `postgres` and `web`; host Nginx remains external.
