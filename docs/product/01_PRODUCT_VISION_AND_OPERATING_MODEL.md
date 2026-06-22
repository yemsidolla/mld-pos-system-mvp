# Product Vision And Operating Model

Status: Implemented (documentation)
Last updated: 2026-06-17

## Product Definition

**Melodu Store Control System** — a simple, beautiful, role-based POS and inventory
control system for pet retail operations.

Melodu POS is the daily operating system for Melodu Pet Store: fast enough for
cashier work, controlled enough for inventory accuracy, and clear enough that
staff, managers, and future AI assistants can understand what changed and why.

The product should favor reliable retail workflows over novelty. Django Admin remains a safety and inspection layer, while the Melodu Dashboard is the primary place for daily work.

## Product Principles

| Principle | Status | Meaning |
| --- | --- | --- |
| Batch-level truth | Implemented | Product records describe items; stock batches are the sellable units. |
| Workflow-generated records | Implemented | Sales, movements, audit logs created by controlled workflows, not imports. |
| Human-readable operations | Implemented | Staff pages use clear labels, obvious actions, visible status. |
| Capability-based access | Implemented | Roles and capabilities decide what a user can see and do. |
| Documentation with every change | Implemented | Implementation updates docs, tasks, and development log. |
| No silent stock changes | Implemented | Stock changes leave movement and audit evidence. |
| Conservative extension | Implemented | Add features around existing services instead of bypassing them. |

## Operating Model

| Role | Main Work | Typical Interfaces | Status |
| --- | --- | --- | --- |
| Owner | Full control, settings, users, reports, audits, recovery | Dashboard, Admin, settings, roles, reports, logs | Current |
| Manager | Daily oversight, sales history, catalog/inventory management, reports | Dashboard, sales, catalog, inventory, reports | Current |
| Inventory Staff | Stock receiving, stock review, labels, adjustments | Stock-in, inventory, labels | Current |
| Cashier | POS selling and receipt workflow | POS and receipt pages | Current |
| Viewer | Read-only sales/report visibility | Reports, sales history | Current |
| AI collaborator | Code/doc review and implementation within governance rules | Repository docs, task tracker, tests | Current |

## Daily Store Workflows

| Workflow | Desired Experience | Status |
| --- | --- | --- |
| Sell item | Scan or type code, choose batch when needed, complete payment, print/view receipt. | Current |
| Receive stock | Choose product/supplier, enter quantity/expiry/cost/price, generate batch code/barcode/QR. | Current |
| Print labels | Select batches/templates, preview, print, audit the print. | Current |
| Manage catalog | Maintain products, categories, brands, animal types, suppliers, tags, images, and reference costs. | Current |
| Upload bulk data | Upload CSV/XLSX, validate, preview, edit/delete rows, commit supported targets. | Current |
| Review inventory | Search products/batches, inspect expiry and stock levels, adjust with reason. | Current |
| Cancel sale | Require reason, restore stock to original batch, audit the cancellation. | Current |
| Report business | Use HTML reports for sales, stock, expiry, movements, and staff activity. | Current |
| Troubleshoot | View live logs and system health, then use runbooks for deployment/backup. | Current |

## Governance Model

New work must follow this path:

1. Read `docs/STANDARD_WAY_OF_WORKING.md`.
2. Check `docs/CURRENT_STATUS.md` and `docs/product/00_CURRENT_SYSTEM_MAP.md`.
3. If UI is affected, check `docs/DESIGN_SYSTEM.md`.
4. Add or update a task in `docs/product/09_IMPLEMENTATION_BACKLOG.md` or `docs/TASKS.md`.
5. Implement the smallest safe change.
6. Run appropriate tests or record why tests were not run.
7. Update documentation and `docs/DEVELOPMENT_LOG.md`.

## Product Boundaries

| Boundary | Status | Notes |
| --- | --- | --- |
| Django monolith | Current | No SPA rewrite, Next.js, Redis, Celery, or microservices unless an ADR changes the decision. |
| Browser-based POS | Current | No native mobile app in the current system. |
| Browser printing | Current | No ESC/POS driver dependency in the current system. |
| Optional OIDC | Current | Local login remains the default and emergency path. |
| Optional MinIO | Current | Media storage can stay local or use S3-compatible object storage. |
| Payment integrations | Future / Proposed | Payment gateways are not implemented. |
| Multi-branch inventory | Future / Proposed | Current model is single-store oriented. |
| Offline POS | Future / Proposed | Current POS requires server/database availability. |

## Success Measures

| Measure | Target | Status |
| --- | --- | --- |
| Staff can complete a sale without Django Admin | Required | Current |
| Stock cannot go negative through normal workflows | Required | Current |
| Every stock change is traceable | Required | Current |
| Important actions are auditable | Required | Current |
| Owner can recover from deployment/data issues using docs | Required | Mostly Current |
| New AI/human team member can understand the system quickly | Required | Current after this reset |
| Mobile scanning works on production devices | Required for scanner-heavy workflows | Needs Verification |
| Backup and restore are rehearsed | Required for production confidence | Needs Verification |
