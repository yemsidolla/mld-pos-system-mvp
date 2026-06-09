# AGENTS.md — Codex & Generic Agent Guide

Instructions for OpenAI Codex and any other autonomous coding agent working on
the **Melodu POS & Inventory Control System**. The full, shared contract for
every contributor (human and AI) is
[`docs/AI_COLLABORATION.md`](docs/AI_COLLABORATION.md). Read it first. This file
is the agent-specific entry point and does not override the charter.

## Project snapshot

Django 5.2 monolith POS/inventory app for Melodu Pet Store. PostgreSQL, Docker
Compose, Gunicorn, WhiteNoise; production HTTPS via **host Nginx** (not a
container). Surfaces: Django Admin (`/admin/`) and the Melodu Dashboard
(`/dashboard/`). Apps: `accounts`, `audit`, `batch_upload`, `catalog`, `core`,
`inventory`, `pos`, `reports`, `system_logs`. Money is `Decimal`; timezone
`Asia/Phnom_Penh`; UI in English + Khmer.

## Your role

You are an **AI Planner / Implementer** (charter §2). You may advance a task
*Pending → AI Planned → AI Generated*. Only a human moves a task to *Done*, and
nothing merges or deploys without owner approval.

## Workflow (charter §3)

Tasks live in `docs/TASKS.md`:

> Pending → AI Planned → AI Generated → Human Reviewing → Fix Required → Testing → Done

- One phase at a time. Do not implement future-phase work early.
- Inspect existing files before changing them.
- Keep each change small, single-concern, reviewable.
- Update `README.md`, `docs/TASKS.md`, and `docs/DEVELOPMENT_LOG.md` after a
  phase or feature.

## Hard rules (must follow — full list in charter §4)

- **`Decimal` for all money. Never `float`.** Timezone `Asia/Phnom_Penh`.
- Batch-level stock: `SaleItem` links to a `StockBatch`; deduct from
  `StockBatch.quantity_available`; never go negative; every stock change creates
  an `InventoryMovement`.
- Wrap stock-in, sale, cancellation, and adjustment in **database transactions**.
- Business logic in **service functions**, not views. Reuse `receive_stock()`,
  sale confirmation, cancellation, and batch-commit services.
- Every important action creates an `AuditLog` via `create_audit_log()`; audit
  logs are read-only in admin.
- **Never log secrets**; redact secret-like values from logs.
- Cashiers reach POS + receipts only — block them from admin, logs, reports,
  inventory, stock-in, sales history, batch upload, system health.
- Keep CSRF enabled. Validate all barcode/QR scan input. Use migrations
  properly.
- Prefer simple Django; no new dependencies or architecture without owner
  approval.

## Build / run / test

```bash
# Local stack (data stays in Docker volumes)
docker compose -f docker-compose.yml -f docker-compose.local.yml up -d --build
docker compose -f docker-compose.yml -f docker-compose.local.yml exec web python manage.py migrate

# Local Django, if deps installed
cd app
python manage.py check
python manage.py test            # or a single app: python manage.py test pos
```

Run `manage.py check` plus the relevant tests before reporting completion. See
`docs/TESTING_GUIDE.md` and `docs/TESTING_CHECKLIST.md`.

## Handoff

When done, leave a note: what changed, files touched, what you tested, what you
did **not** test, and the next step. Never report a task as done or tested if it
was not. Shared state lives in the repo files, not in your memory — keep
`docs/TASKS.md` and `docs/DEVELOPMENT_LOG.md` current so the next contributor can
continue.
