# QA And Release Process

Status: Implemented (documentation)
Last updated: 2026-06-17

This process defines how Melodu POS changes should be checked and released. It complements `docs/STANDARD_WAY_OF_WORKING.md`.

## Release Gates

| Gate | Required For | Status |
| --- | --- | --- |
| Scope review | Every change | Current |
| Source inspection | Every change | Current |
| Unit/service tests | Model, service, stock, sales, auth, upload, scanner resolver changes | Current |
| Template/view tests | Dashboard route or permission changes | Current |
| Browser/mobile verification | UI, scanner, print, navigation, responsive changes | Current |
| Migration review | Schema changes | Current |
| Docs update | Every product-visible or operational change | Current |
| Development log entry | Every implementation milestone | Current |
| Backup/restore review | Deployment, storage, data reset, or migration work | Current |

## Standard QA Matrix

| Change Type | Minimum Checks |
| --- | --- |
| Markdown-only docs | Review file structure, required sections, links, and git diff. Django tests are not required. |
| Backend model/service | `python manage.py check`, targeted tests, related integration tests. |
| Stock/sales workflow | Targeted service tests plus full suite when feasible. |
| Permission/auth | Role/capability tests, login/logout checks, denial audit checks. |
| Dashboard UI | Template render tests, browser screenshot/check on desktop and mobile. |
| Scanner | Resolver tests, decode tests, browser check, real phone verification when possible. |
| Media/storage | Local and S3/MinIO checks, upload/display tests, backup notes. |
| Deployment | Compose config, build, migrate, collectstatic, health, login, static/media checks. |
| Reset/backup | Dry run, non-production restore rehearsal, audit check. |

## Documentation-Only Validation

Use this when the change is strictly Markdown/docs and the plan forbids app changes.

1. Confirm changed paths are limited to allowed docs.
2. Confirm required files exist.
3. Confirm each new doc has status and date.
4. Confirm links use existing paths or clearly future/proposed references.
5. Confirm links use paths from `docs/README.md` and `docs/product/11_DOCUMENTATION_MAP.md`.
6. Confirm `docs/DESIGN_SYSTEM.md` is unchanged if the task says not to touch it.
7. Confirm `git diff --name-only` shows only documentation/README paths.
8. Record that Django tests were not run because no app code changed.

## Application Validation

For implementation changes, use this baseline unless a narrower documented test plan is approved.

```bash
docker compose run --rm web python manage.py check
docker compose run --rm web python manage.py test
```

For production compose or MinIO-sensitive work, also check:

```bash
docker compose --env-file .env.example -f docker-compose.prod.yml config --services
docker compose run --rm -e USE_S3_MEDIA=True web python manage.py check
```

## Release Checklist

| Item | Status |
| --- | --- |
| Task scope is clear and does not add unapproved requirements. | Current |
| Source files were inspected before editing. | Current |
| App behavior changes have tests or documented reason tests were not run. | Current |
| UI changes follow `docs/DESIGN_SYSTEM.md`. | Current |
| Data migrations are reviewed and reversible/understood. | Current |
| Permissions are tested for allowed and denied roles. | Current |
| Deployment commands are documented if deployment behavior changes. | Current |
| Backup/restore impact is documented for data/storage changes. | Current |
| Docs and task tracker are updated. | Current |
| `docs/DEVELOPMENT_LOG.md` has a milestone entry. | Current |

## Production Smoke Test

After deploy, verify:

| Check | Status |
| --- | --- |
| Login works on production domain. | Needs Verification |
| CSRF trusted origin matches production domain. | Needs Verification |
| Static files load. | Needs Verification |
| Media files load from active storage backend. | Needs Verification |
| Dashboard home opens for Owner/Manager/Cashier sample users. | Needs Verification |
| POS can add and complete a test sale in a safe environment. | Needs Verification |
| Stock-in can receive a safe test batch. | Needs Verification |
| Reports render. | Needs Verification |
| Audit log records critical actions. | Needs Verification |
| Live logs and health pages are access-controlled. | Needs Verification |
| Backup command succeeds. | Needs Verification |

## Release Notes Format

Use this shape for future releases:

```text
Version:
Date:
Scope:
Changed:
Fixed:
Docs:
Tests:
Deployment notes:
Known risks:
Rollback:
```
