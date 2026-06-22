# V6 As-Built Review

Status: Current
Last updated: 2026-06-16

This review records what the current codebase contains at the time of the controlled foundation reset.

## Architecture As Built

| Area | As Built | Status |
| --- | --- | --- |
| App pattern | Django monolith with app modules. | Current |
| UI pattern | Django templates with shared dashboard shell. | Current |
| Database | PostgreSQL. | Current |
| Runtime | Docker Compose and Gunicorn. | Current |
| Public proxy | Host Nginx expected for production HTTPS. | Current |
| Static | WhiteNoise. | Current |
| Media | Filesystem or optional MinIO/S3-compatible storage. | Current |
| I18n | English and Khmer configured through Django i18n. | Mostly Current |

## Apps As Built

| App | Observed Responsibility | Status |
| --- | --- | --- |
| `accounts` | Roles, staff profiles, OIDC backend, role setup commands. | Current |
| `audit` | Audit log model/helper/signals/admin. | Current |
| `batch_upload` | Staged CSV/XLSX upload workflows. | Current |
| `catalog` | Products, categories, brands, suppliers, reference costs, tags, animal types. | Current |
| `core` | Dashboard views, settings, permissions, context, scanner API, reset command. | Current |
| `inventory` | Stock batches, movements, stock-in and inventory workflows. | Current |
| `labels` | Label templates and print workflows. | Current |
| `pos` | Sales, sale items, promotions, receipts, cancellation. | Current |
| `reports` | HTML reports. | Current |
| `system_logs` | Live log/system troubleshooting pages. | Current |

## Auth And Authorization As Built

| Area | Observed Behavior | Status |
| --- | --- | --- |
| Local login | Default authentication path. | Current |
| Authentik/OIDC | Enabled when `AUTH_MODE=oidc`; backend maps claims/groups to users/roles. | Current |
| Local fallback | `LOCAL_LOGIN_ENABLED` controls emergency local path. | Current |
| Roles | Owner, Manager, Inventory Staff, Cashier, Viewer. | Current |
| Capabilities | Data-driven role capabilities plus profile overrides. | Current |
| Legacy support | Admin/Cashier groups map to modern access behavior. | Current |
| Superuser | Resolves to Owner behavior. | Current |
| Cashier Admin block | Middleware blocks cashier access to Django Admin. | Current |
| Production OIDC claim mapping | Requires real Authentik verification. | Needs Verification |

## Inventory As Built

| Area | Observed Behavior | Status |
| --- | --- | --- |
| Product master data | Product records define catalog data only. | Current |
| Stock batch | Batch is sellable unit with supplier, expiry, quantity, cost, price, code/images/status. | Current |
| Stock movement | Movement records represent stock-changing actions. | Current |
| Stock-in | Creates batch, barcode, QR, movement, and audit. | Current |
| Sale | Deducts stock from selected batch. | Current |
| Cancellation | Restores stock to original batch and audits. | Current |
| Adjustment | Requires reason and prevents negative stock. | Current |
| Expiry | Expiry status and maintenance command exist. | Current |

## Catalog As Built

| Area | Observed Behavior | Status |
| --- | --- | --- |
| Master data | Categories, brands, suppliers, products. | Current |
| Product image | Product image field and optional MinIO storage support. | Current |
| Classification | Animal types M2M, life stage, tags. | Current |
| Animal type management | Dashboard management and quick-add exist. | Current |
| Supplier costs | Reference cost model/workflows exist. | Current |
| Product upload | Batch upload includes product and classification fields. | Current |

## Dashboard As Built

| Area | Observed Behavior | Status |
| --- | --- | --- |
| Shared shell | Sidebar, mobile nav, top action bar, dashboard components. | Current |
| Role-aware navigation | Navigation is built from capability context. | Current |
| Scanner modal | Reusable scanner modal and local vendor scanner library. | Current |
| Image decode | Server-side image decode endpoint exists. | Mostly Current |
| Design system | Dedicated design-system doc and style guide page exist. | Current |
| Mobile behavior | Mobile nav and table overflow support exist. | Mostly Current |

## Operations As Built

| Area | Observed Behavior | Status |
| --- | --- | --- |
| Health endpoint | `/health/` exists. | Current |
| Live logs | Dashboard live logs page exists. | Current |
| System health | Dashboard system health page exists. | Current |
| Deployment docs | Deployment guide/runbook/checklists exist. | Mostly Current |
| Backup scripts | Database, filesystem media, and MinIO backup/restore scripts exist. | Current |
| Backup rehearsal | Must be verified in a non-production clone. | Needs Verification |

## Documentation As Built

| Area | Observed Behavior | Status |
| --- | --- | --- |
| Standard way of working | Exists and is the first governance reference. | Current |
| Current status | Exists and is updated by this reset. | Current |
| Design system | Exists and remains unchanged. | Current |
| Feature guides | Batch upload, MinIO, labels, receipts, permissions, reset, product classification, deployment. | Current |
| Version docs | V2-V6 docs exist; some overlap with current product docs. | Duplicate / Overlapping |
| ADRs | Added by this reset. | Current |

## Open Verification Items

| Item | Status |
| --- | --- |
| Production Authentik group claim shape and role sync. | Needs Verification |
| Production host Nginx headers, CSRF trusted origin, secure cookie behavior. | Needs Verification |
| Production media endpoint and MinIO public URL behavior. | Needs Verification |
| Existing filesystem media migration to MinIO. | Needs Verification |
| Phone camera and uploaded-image scanner decode across real devices. | Needs Verification |
| Physical receipt and label printer output. | Needs Verification |
| Full backup/restore rehearsal. | Needs Verification |
