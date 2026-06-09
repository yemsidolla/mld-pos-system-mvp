# CLAUDE.md — Claude Code Guide

Instructions for Claude Code working on the **Melodu POS & Inventory Control
System**. The full, shared contract for every contributor (human and AI) is
[`docs/AI_COLLABORATION.md`](docs/AI_COLLABORATION.md). Read it. This file is the
Claude-specific entry point and does not override the charter.

## Project in one paragraph

Django 5.2 monolith POS/inventory app for Melodu Pet Store. PostgreSQL, Docker
Compose, Gunicorn, WhiteNoise; production HTTPS via host Nginx (not a container).
Two surfaces: Django Admin (`/admin/`) and the Melodu Dashboard (`/dashboard/`).
Apps: `accounts`, `audit`, `batch_upload`, `catalog`, `core`, `inventory`,
`pos`, `reports`, `system_logs`. Money is `Decimal`; timezone `Asia/Phnom_Penh`;
UI in English + Khmer.

## Your role

You act as **AI Planner** and **AI Implementer** (see charter §2). You may move a
task from *Pending → AI Planned → AI Generated*. Only a human marks a task
*Done*. Nothing ships without the owner's approval.

## Before you code

1. Read `README.md` and `docs/PROJECT_SPEC.md` for the current phase and version
   boundary.
2. Inspect the existing models, `services.py`, views, templates, and tests in the
   app you'll touch — do not guess.
3. For non-trivial work, lay out a short plan and the files you'll change, then
   proceed. Use plan mode when the scope is unclear or risky.

## Hard rules (must follow — full list in charter §4)

- **`Decimal` for all money. Never `float`.** Timezone `Asia/Phnom_Penh`.
- Stock is batch-level: `SaleItem` links to a `StockBatch`; deduct from
  `StockBatch.quantity_available`; stock never goes negative; every stock change
  creates an `InventoryMovement`.
- Wrap stock-in, sale, cancellation, and adjustment in **DB transactions**.
- Business logic lives in **service functions**, not views. Reuse existing
  services (`receive_stock()`, sale confirmation, cancellation, batch commit).
- Every important action creates an `AuditLog` via `create_audit_log()`. Audit
  logs are read-only in admin.
- **Never log secrets** (passwords, tokens, keys); redact secret-like values.
- Cashiers reach POS + receipts only — never admin, logs, reports, inventory,
  stock-in, sales history, batch upload, or system health.
- Keep CSRF on. Validate all barcode/QR input. Use migrations properly.
- Prefer simple Django solutions; do not add dependencies or architecture
  without owner approval. One phase at a time — no future-phase work early.

## Build / run / test

Local stack (OneDrive-synced workspace):

```bash
docker compose -f docker-compose.yml -f docker-compose.local.yml up -d --build
docker compose -f docker-compose.yml -f docker-compose.local.yml exec web python manage.py migrate
```

Local Django (if deps installed):

```bash
cd app
python manage.py check
python manage.py test          # or: python manage.py test pos
```

Run `manage.py check` and the relevant tests before reporting a change complete.
See `docs/TESTING_GUIDE.md`.

## When you finish

Update `docs/TASKS.md`, `docs/DEVELOPMENT_LOG.md`, and `README.md` if behavior
changed. Give a handoff note: what changed, files touched, what you tested, what
you did **not** test, and the suggested next step. Be honest — never claim
something is done or tested when it isn't.
