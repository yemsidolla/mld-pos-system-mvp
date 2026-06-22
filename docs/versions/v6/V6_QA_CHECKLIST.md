# V6 QA Checklist

Status: Current
Last updated: 2026-06-16

This checklist validates the controlled foundation reset. Because this reset is documentation-only, Django tests are not required unless application files change accidentally.

## Documentation Structure

| Check | Status |
| --- | --- |
| `docs/product/` exists. | Current |
| `docs/product/00_CURRENT_SYSTEM_MAP.md` exists. | Current |
| `docs/product/01_PRODUCT_VISION_AND_OPERATING_MODEL.md` exists. | Current |
| `docs/product/04_MODULE_MAP.md` exists. | Current |
| `docs/product/05_BRD.md` exists. | Current |
| `docs/product/06_PRD.md` exists. | Current |
| `docs/product/07_TRD.md` exists. | Current |
| `docs/product/08_VERSION_ROADMAP.md` exists. | Current |
| `docs/product/09_IMPLEMENTATION_BACKLOG.md` exists. | Current |
| `docs/product/10_QA_RELEASE_PROCESS.md` exists. | Current |
| `docs/product/11_DOCUMENTATION_MAP.md` exists. | Current |
| `docs/versions/v6/` exists. | Current |
| All five required V6 reset docs exist. | Current |
| `docs/decisions/` exists. | Current |
| ADR-0001 through ADR-0007 exist. | Current |

## Content Checklist

| Check | Status |
| --- | --- |
| New docs include a status and last-updated date. | Current |
| Status labels use the approved set. | Current |
| Documentation map includes the required read order. | Current |
| Current system map uses source code as source of truth. | Current |
| Uncertain behavior is marked `Needs Verification`. | Current |
| V7/V8/V9/V10 items are roadmap/backlog only. | Current |
| `docs/DESIGN_SYSTEM.md` remains unchanged. | Needs Verification |
| Older docs organized under `docs/legacy/`. | Current |

## Supporting Entry Docs

| Check | Status |
| --- | --- |
| README contains a compact documentation map link section. | Current |
| `docs/CURRENT_STATUS.md` points to new authoritative maps. | Current |
| `docs/CURRENT_STATUS.md` no longer contains stale uncommitted-change notes. | Current |
| `docs/TASKS.md` tracks the foundation reset. | Current |
| `docs/DEVELOPMENT_LOG.md` records the reset milestone. | Current |

## Git Diff Checklist

Run:

```bash
git diff --name-only
```

Expected changed paths:

```text
README.md
docs/CURRENT_STATUS.md
docs/DEVELOPMENT_LOG.md
docs/TASKS.md
docs/decisions/*
docs/product/*
docs/versions/v6/*
```

If any application file changes accidentally, stop and run:

```bash
docker compose run --rm web python manage.py check
docker compose run --rm web python manage.py test
```

## Test Decision

| Check | Status | Reason |
| --- | --- | --- |
| Django tests | Current | Not required for Markdown-only documentation reset. |
| Documentation validation | Needs Verification | Run structure/link/diff checks before final handoff. |
