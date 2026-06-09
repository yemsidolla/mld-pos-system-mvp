# AI & Human Collaboration Charter

This is the single source of truth for how every contributor — human or AI
(Claude Code, OpenAI Codex, Cursor, or any other assistant) — works on the
Melodu POS & Inventory Control System.

Tool-specific entry points all defer to this document:

- `CLAUDE.md` — Claude Code
- `AGENTS.md` — Codex and other generic coding agents
- `.cursor/rules/melodu-pos.mdc` — Cursor

If any tool file disagrees with this charter, this charter wins. Keep them in
sync: when a rule changes here, update the others in the same change.

---

## 1. What This Project Is

A Django monolith POS and inventory system for Melodu Pet Store.

- **Stack:** Django 5.2 (Python), PostgreSQL, Docker Compose, Gunicorn,
  WhiteNoise. Production HTTPS is terminated by **host Nginx**, not a container.
- **Two surfaces:** Django Admin (`/admin/`) for raw model management, and the
  Melodu Dashboard (`/dashboard/`) for daily POS, stock-in, inventory, reports,
  labels, batch upload, live logs, and system health.
- **Django apps:** `accounts`, `audit`, `batch_upload`, `catalog`, `core`,
  `inventory`, `pos`, `reports`, `system_logs`, plus the `melodu_pos` project.
- **Money is `Decimal`. Timezone is `Asia/Phnom_Penh`. Languages: English + Khmer.**

Read `README.md` and `docs/PROJECT_SPEC.md` before writing code. They describe
the implemented phases and the boundaries of each version.

---

## 2. Roles

Everyone — human and AI — shares one goal: ship small, correct, reviewable
changes one phase at a time. Roles describe *responsibility*, not *permission to
skip review*.

| Role | Who | Responsibility |
| --- | --- | --- |
| **Owner / Product** | Human | Approves phases, sets priorities, gives final sign-off. Nothing ships without owner approval. |
| **AI Planner** | Any AI | Reads the spec and existing code, proposes a plan, lists files to touch, surfaces risks. Plans, does not merge. |
| **AI Implementer** | Any AI | Writes the smallest change that satisfies the approved plan. Inspects files first, follows the rules below, reports honestly what was and was not tested. |
| **Human Reviewer** | Human (or a second AI doing review) | Reviews the diff against the spec and the rules, runs/verifies tests, requests fixes. |
| **Maintainer** | Human | Owns migrations, deployment, secrets, and the production database. |

AIs may move a task through *AI Planned → AI Generated*. Only a human moves a
task to *Done*.

---

## 3. Workflow (the contract)

Tasks live in `docs/TASKS.md`. Statuses, in order:

> Pending → AI Planned → AI Generated → Human Reviewing → Fix Required → Testing → Done

1. **One phase at a time.** Do not start the next phase until the current phase
   is tested and approved by the owner. Do not implement future-phase work early.
2. **Inspect before you change.** Read the existing models, services, views,
   templates, and tests in the app you are touching before editing.
3. **Plan, then implement.** For anything non-trivial, state the plan and the
   files you will touch, and wait for approval if the scope is unclear.
4. **Keep changes small and reviewable.** One concern per change. Prefer simple
   Django solutions over new architecture or new dependencies.
5. **Update the paper trail.** After a phase or feature, update `README.md`,
   `docs/TASKS.md`, and `docs/DEVELOPMENT_LOG.md` to match reality.
6. **Be honest about testing.** Never claim a task is done if it was not tested.
   If you could not run something, say so explicitly.

---

## 4. Hard Rules (never break these)

These come from `docs/CODEX_RULES.md` and the project spec. They are
non-negotiable for every contributor.

**Money & time**
- Use `Decimal` for all prices and amounts. **Never use `float` for money.**
- Use timezone `Asia/Phnom_Penh`.

**Stock integrity (the core business rule)**
- All stock is controlled at **stock batch** level.
- `Product` is master data; `StockBatch` is real sellable stock.
- `SaleItem` must always link to a `StockBatch`. Deduct stock only from
  `StockBatch.quantity_available`.
- Stock quantity must **never** go negative.
- Every stock change must create an `InventoryMovement`.
- Wrap stock-in, sale, cancellation, and adjustment in **database transactions**.

**Business logic placement**
- Keep business logic in **service functions** (e.g. `app/<app>/services.py`,
  `pos/pricing.py`), not inside views. Reuse existing services
  (`receive_stock()`, sale confirmation, cancellation, batch commit) rather than
  re-implementing them.

**Audit & logging**
- Every important business action must create an `AuditLog` via
  `create_audit_log()`.
- Audit logs are read-only in normal admin (no add/delete).
- Every backend error must be written to logs.
- **Never log passwords, tokens, secret keys, or other credentials.** Redact
  secret-like values from any log output.

**Permissions & security**
- Cashiers can access POS and receipts only. They must **not** reach audit logs,
  backend/live logs, system health, inventory, reports, stock-in, labels, sales
  history, batch upload, user management, or Django Admin.
- Superusers and `Admin` group members access management pages.
- Keep CSRF middleware enabled. Validate all barcode and QR scan input.

**Migrations & data**
- Use Django migrations properly; never hand-edit the database schema.
- Do not commit secrets. `.env` is local only; keep `.env.example` accurate.

---

## 5. How to Build, Run, and Test

Local development (OneDrive-synced workspace; data stays in Docker volumes):

```bash
docker compose -f docker-compose.yml -f docker-compose.local.yml up -d --build
docker compose -f docker-compose.yml -f docker-compose.local.yml exec web python manage.py migrate
docker compose -f docker-compose.yml -f docker-compose.local.yml exec web python manage.py collectstatic --noinput
```

If dependencies are installed locally:

```bash
cd app
python manage.py check
python manage.py test
```

Run a single app's tests:

```bash
cd app
python manage.py test pos
```

Always run `python manage.py check` and the relevant tests before reporting a
change as complete. See `docs/TESTING_GUIDE.md` and `docs/TESTING_CHECKLIST.md`.

Production uses `docker-compose.prod.yml` with host Nginx pointing at
`127.0.0.1:${WEB_HOST_PORT}`. See `docs/DEPLOYMENT_GUIDE.md` and
`docs/PRODUCTION_CHECKLIST.md`.

---

## 6. Working With Each Other (AI ↔ AI ↔ Human)

- **Shared state lives in files, not memory.** `docs/TASKS.md` is the handoff
  board; `docs/DEVELOPMENT_LOG.md` is the history. Update them so the next
  contributor (human or AI) can pick up cleanly.
- **Leave a handoff note.** When you finish, state: what changed, which files,
  what you tested, what you did *not* test, and the suggested next step.
- **Don't undo another contributor's work silently.** If you must change
  something a previous commit added, explain why.
- **Ask when the spec is ambiguous.** A short question to the owner beats a wrong
  assumption baked into a migration.
- **Respect approval gates.** Migrations, deployments, schema changes, and
  anything touching production data wait for explicit human approval.
- **Match the surrounding code.** Mirror existing naming, structure, comment
  density, and Django idioms in the file you are editing.

---

## 7. Key Documents

| Topic | File |
| --- | --- |
| Project overview & setup | `README.md` |
| Full spec & implemented phases | `docs/PROJECT_SPEC.md` |
| Business rules | `docs/BUSINESS_RULES.md` |
| Task board | `docs/TASKS.md` |
| Development history | `docs/DEVELOPMENT_LOG.md` |
| Testing | `docs/TESTING_GUIDE.md`, `docs/TESTING_CHECKLIST.md` |
| Permissions / dashboard access | `docs/DASHBOARD_ACCESS_RULES.md` |
| Batch upload | `docs/BATCH_UPLOAD_GUIDE.md` |
| Deployment | `docs/DEPLOYMENT_GUIDE.md`, `docs/DEPLOYMENT_RUNBOOK.md` |
| Backup & restore | `docs/BACKUP_GUIDE.md` |
| Original concise rules | `docs/CODEX_RULES.md` |
