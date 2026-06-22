# V10 Release Note

Status: Complete
Last updated: 2026-06-16

## Version Summary

V10 prepared Melodu POS for future scale and multi-store direction while protecting the current single-store Django monolith.

## What Changed

- Added a multi-store readiness audit showing current single-store assumptions across settings, roles, catalog, stock, sales, promotions, labels, batch upload, audit, reports, and deployment.
- Added future store/location model planning with migration/backfill risks.
- Added future store-level permission, inventory, and reporting plans.
- Added store settings separation review for receipt, logo, KHQR, quick keys, cost visibility, and auth settings.
- Added deployment/backup hardening review.
- Added monitoring/logging scale-readiness review.
- Added data retention and audit retention plan.
- Added performance/database review.
- Added ADR-0008 to make clear that V10 planning does not implement multi-store behavior.
- Updated V10 task statuses, QA checklist, version tracker, and development log.

## What Did Not Change

- No full multi-store implementation.
- No `Store` or `Location` model.
- No database migrations.
- No store foreign keys.
- No store selector.
- No permission behavior changes.
- No POS, stock-in, inventory, label, report, audit, user-management, settings, or system-health behavior changes.
- No complex warehouse management.
- No ERP or accounting integration.
- No microservices migration.
- No new frontend framework.
- No mobile app rewrite.
- No major infrastructure migration.

## Risk Level

Low for this release because V10 is documentation/planning only.

Future implementation risk is high if store schema, permissions, deployment, or retention behavior is implemented without the V10 migration and permission guardrails.

## Testing Notes

- Documentation structure and diff validation completed.
- No V10 application tests were required because no V10 application behavior changed.
- The broader V9 close immediately before V10 passed mounted-source `manage.py check`, `collectstatic --noinput`, and the full 319-test Django suite.

## Rollback Note

V10 docs can be reverted normally. No schema, permission, deployment, or retention rollback is required because none was changed.

## Recommended Next Version

Next scale implementation must be defined only after V10 decisions are reviewed and a specific model/permission/migration/report scope is approved.
