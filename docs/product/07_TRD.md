# Technical Requirements Document

Status: Current
Last updated: 2026-06-17

## Purpose

This TRD records the technical shape of the current Melodu POS implementation and the constraints future work must respect.

## Architecture

| Layer | Current Choice | Status |
| --- | --- | --- |
| App architecture | Django monolith | Current |
| UI architecture | Django templates, shared dashboard shell, static CSS, vanilla JavaScript | Current |
| Database | PostgreSQL | Current |
| Runtime | Docker Compose, Gunicorn | Current |
| Public reverse proxy | Host Nginx terminates HTTPS | Current |
| Static files | WhiteNoise compressed manifest storage | Current |
| Media storage | Filesystem or optional S3-compatible MinIO | Current |
| Authentication | Django auth with optional `mozilla_django_oidc` backend | Current |
| Authorization | Role/capability helpers and decorators | Current |
| Internationalization | Django i18n, English and Khmer language settings | Current |

## Application Requirements

| Requirement | Status | Notes |
| --- | --- | --- |
| App code must stay in the Django monolith unless an ADR changes direction. | Current | ADR-0001 records this decision. |
| Daily business workflows must use dashboard views, not raw Admin-only flows. | Current | Admin remains for raw inspection and emergency operations. |
| Stock-changing services must use database transactions. | Current | Preserve for stock-in, sale, cancellation, adjustment. |
| Barcode/QR, movement, and audit creation should be part of business transactions where possible. | Current | Stock-in upload must continue using `receive_stock()`. |
| Upload commit must not bypass validation/services. | Current | Batch upload staging is the control boundary. |
| Money calculations must use Decimal. | Current | Do not introduce floats. |
| Scanner APIs must remain read-only except where explicit workflow submission commits data. | Current | Resolver does not mutate data. |
| Logs visible in dashboard must not expose secrets. | Mostly Current | Continue reviewing as logging evolves. |

## URL And Routing Requirements

| Requirement | Status |
| --- | --- |
| `/dashboard/` is the primary authenticated work area. | Current |
| `/admin/` remains available for staff who should use Django Admin. | Current |
| `/health/` remains a lightweight infrastructure health endpoint. | Current |
| `/dashboard/api/scan/resolve/` remains read-only. | Current |
| `/dashboard/api/scan/decode-image/` must require authentication. | Current |
| `/dashboard/pos/receipt/<sale_id>/` is the receipt route after sale confirm. | Current |
| `/media/<path>` serves protected media to authenticated staff. | Current |
| OIDC routes are mounted only when OIDC app/routes are enabled. | Current |

## Data Integrity Requirements

| Requirement | Status | Notes |
| --- | --- | --- |
| `SaleItem` must link to `StockBatch`. | Current | Required for reversal and auditability. |
| `StockBatch.quantity_available` must not go below zero. | Current | Enforced by constraints and services. |
| `StockBatch.quantity_received` must be positive. | Current | Enforced by constraints. |
| `InventoryMovement` must record stock-changing actions. | Current | Required for stock ledger. |
| `AuditLog` must record critical user/system actions. | Current | Use helper functions. |
| Product original barcode uniqueness must be preserved. | Current | Upload and form validation must surface conflicts. |
| Existing migrations are part of history and must not be rewritten casually. | Current | New schema changes require migrations/tests/docs. |

## Authentication Requirements

| Requirement | Status |
| --- | --- |
| `AUTH_MODE=local` uses Django username/password authentication. | Current |
| `AUTH_MODE=oidc` prepends the Melodu OIDC backend. | Current |
| OIDC should auto-create users only when configured. | Current |
| OIDC group sync should map Authentik groups to Melodu roles. | Current |
| Superuser role behavior must remain protected from accidental downgrade. | Current |
| Local login should remain available during OIDC rollout unless intentionally disabled. | Current |
| Production OIDC claims must be verified before disabling local emergency login. | Needs Verification |

## Authorization Requirements

| Requirement | Status |
| --- | --- |
| Superusers resolve to Owner capability behavior. | Current |
| StaffProfile role is the primary dashboard authorization source. | Current |
| Legacy Admin/Cashier groups remain compatibility inputs. | Current |
| Owner-only role management must remain protected. | Current |
| Cashier users are restricted to POS-focused workflows. | Current |
| Capability checks must be added to new dashboard views. | Current |
| Permission denial should create audit evidence for sensitive attempts. | Current |
| Capability keys are defined in `app/core/capabilities.py`; do not rename without migration. | Current |

Canonical capability keys: `pos.access`, `pos.override_below_cost`, `sales.view_history`,
`sales.cancel`, `sales.reprint`, `catalog.manage`, `promotions.manage`,
`inventory.manage`, `reports.view`, `system.manage_users`, `system.manage_settings`,
`system.view_audit`, `system.view_logs`, `system.reset_data`.

## Frontend Requirements

| Requirement | Status | Authority |
| --- | --- | --- |
| Use the shared dashboard shell for business pages. | Current | `docs/DESIGN_SYSTEM.md` |
| Use shared buttons, badges, tables, forms, alerts, empty states, and modals. | Current | `docs/DESIGN_SYSTEM.md` |
| Avoid one-off inline styling where shared classes exist. | Mostly Current | Ongoing cleanup as pages evolve. |
| Maintain mobile layout and bottom navigation. | Current | Dashboard shell |
| Scanner buttons should open the reusable scanner modal. | Current | Scanner JS/templates |
| Use local vendor assets instead of CDN for scanner library. | Current | Static vendor asset |

## Storage Requirements

| Requirement | Status |
| --- | --- |
| Filesystem media mode must work for development and simple deployments. | Current |
| MinIO/S3 media mode must work for larger product image workflows. | Current |
| Static assets must be collected and served consistently. | Current |
| Media URLs must be reachable over HTTPS in production. | Needs Verification |
| Existing local media migration to MinIO must be deliberate and backed up. | Needs Verification |

## Deployment Requirements

| Requirement | Status |
| --- | --- |
| VPS deployment uses Docker Compose for app/database/object storage. | Current |
| Host Nginx handles HTTPS and proxy headers. | Current |
| `DJANGO_ALLOWED_HOSTS` and `DJANGO_CSRF_TRUSTED_ORIGINS` must match production domains. | Current |
| Secure cookies should be enabled behind HTTPS in production. | Current |
| Migrations must run before creating users or using the app. | Current |
| Static collection must run after deploy/build. | Current |
| Backup scripts must be available and documented. | Current |
| Restore must be rehearsed outside production. | Needs Verification |

## Testing Requirements

| Area | Minimum Test Expectation | Status |
| --- | --- | --- |
| Models and services | Unit tests for validation, transactions, stock and audit behavior. | Current |
| Permissions | Role/capability view tests and denial tests. | Current |
| Uploads | Parser, validation, preview, edit/delete, and commit tests. | Current |
| Scanner | Resolver/decode tests plus browser/device verification. | Mostly Current |
| UI changes | Template render tests and screenshot/browser checks for risky visual changes. | Mostly Current |
| Deployment | `manage.py check`, migrations, collectstatic, health endpoint. | Current |
| Full suite | `python manage.py test` — ~297 test methods across 10 custom apps. | Current |

## Technical Debt And Verification Items

| Item | Status | Notes |
| --- | --- | --- |
| Full Khmer translation completeness | Needs Verification | Language support exists; strings should be reviewed. |
| Production phone scanner matrix | Needs Verification | Test Android/iOS browsers against camera and upload decode. |
| Printer hardware output matrix | Needs Verification | Browser print layout needs physical verification. |
| Log secret redaction | Needs Verification | Review live log output under real errors. |
| Backup restore rehearsal | Needs Verification | Required before production confidence. |
| Report business definitions | Needs Verification | Confirm with store owner/accounting needs. |
| Refund workflow | Missing | `Sale.Status.REFUNDED` exists in models but no refund service/view found. |
