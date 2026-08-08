# Tailwind CSS workflow (Melodu POS)

Tailwind **standalone CLI** builds CSS at image build time.
**No Node, no npm, no `package.json`.** The runtime Docker image is Python-only.

Pinned version: **v4.3.3** (verified via GitHub Releases API
`GET /repos/tailwindlabs/tailwindcss/releases/latest` on 2026-08-06; asset
checksums from that release’s `sha256sums.txt`). Configuration is CSS-first
(`@theme` in `input.css`) — there is no `tailwind.config.js`.

## Cascade layers (important)

`dashboard.css` is **not** linked directly. `cascade.css` imports it into
`@layer legacy`, declared before Tailwind’s `utilities` layer. Utilities therefore
win without a global `important` on every utility. Do not re-add
`@import "tailwindcss/utilities.css" … important`.

| Path | Role |
| --- | --- |
| `app/core/static/core/css/cascade.css` | `@layer` order + `@import` of `dashboard.css` into `legacy` |
| `tailwind/input.css` | Source: `@theme` Melodu tokens + imports (not collected as static) |
| `app/core/static/core/css/tailwind.css` | Generated utilities (committed; Docker rebuilds) |
| `app/core/static/core/css/dashboard.css` | Legacy design-system CSS (still required for unmigrated screens) |
| `scripts/build_tailwind.sh` | Local download (pinned) + build / watch |
| `docker/django/Dockerfile` | Multi-stage: build CSS, copy into Python image |

Token → utility mapping: `docs/DESIGN_SYSTEM.md` §2.0.

## Local development (watch mode)

While editing templates:

```bash
./scripts/build_tailwind.sh --watch
```

This downloads the pinned standalone binary into `.tools/` on first run (gitignored),
then rebuilds `tailwind.css` whenever template or `input.css` classes change.

One-shot minify build (same as CI/Docker intent):

```bash
./scripts/build_tailwind.sh
```

Override the pin only for experiments:

```bash
TAILWIND_VERSION=4.3.3 ./scripts/build_tailwind.sh
```

## Before committing

1. Run `./scripts/build_tailwind.sh` so `tailwind.css` matches `input.css` + templates.
2. Remove from `dashboard.css` only rules that are fully migrated to utilities.
3. Spot-check `/dashboard/styleguide/`, `/dashboard/`, and `/dashboard/users/`
   (owner/manager) after `collectstatic` / container rebuild so hashed static
   files refresh.

## Docker

`docker/django/Dockerfile` stage `tailwind` fetches
`tailwindcss-linux-{x64|arm64}` for `TAILWIND_VERSION=4.3.3`, verifies
`sha256sum`, compiles `tailwind.css`, and copies **only** that file into the
final `python:3.12-slim` image. The runtime image must not contain `node`.

```bash
WEB_HOST_PORT=8010 docker compose -f docker-compose.yml -f docker-compose.local.yml build --no-cache web
WEB_HOST_PORT=8010 docker compose -f docker-compose.yml -f docker-compose.local.yml up -d
docker compose -f docker-compose.yml -f docker-compose.local.yml exec web \
  sh -c 'command -v node || echo NO-NODE'
docker compose -f docker-compose.yml -f docker-compose.local.yml exec web \
  python manage.py collectstatic --noinput
```

## Scope reminder

Migrated to utilities (phase 2): dashboard shell (`base.html`), home KPI cards,
role badges (shared include), and matching styleguide samples. Do not migrate
POS/till, receipts, or labels until a later approved phase.
