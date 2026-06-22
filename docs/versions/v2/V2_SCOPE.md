# V2 Scope — Stabilization, Safety, Reports, and Backup Baseline

## Status

Historical / Completed

## Version Goal

Stabilize the V1 foundation: document the as-built system, harden backup/restore,
correct stock report logic, and improve dashboard access before bigger features.

## Why This Version Existed

V1 grew quickly. V2 focused on safety, operational clarity, and low-risk UX fixes
without changing core sale/inventory rules.

## In Scope

| Area | Status |
| --- | --- |
| V2 baseline audit documentation | Implemented |
| Active/sellable stock report rules | Implemented |
| `expire_batches` management command | Implemented |
| Backup/restore script hardening | Implemented |
| Dashboard login/logout (`/dashboard/login/`) | Implemented |
| Friendly 403/404/500 pages | Implemented |
| Catalog quick-create (category/brand/supplier) | Implemented |
| POS empty states and double-submit protection | Implemented |
| Report export planning (backlog) | Documented Only |

## Out Of Scope

Major UI redesign, Authentik/OIDC, promotions, full permission matrix, multi-store.

## Source Evidence

- `docs/legacy/V2_BASELINE_AUDIT.md`
- `docs/DEVELOPMENT_LOG.md` — 2026-06-09 V2 entries
- `docs/legacy/V2_PHASE_2A_ACCESS_POS_UX.md`, `V2_PHASE_2B_DASHBOARD_ACCESS_POS_UX.md`

## Major Modules Affected

`core` (login, permissions UX), `reports`, `catalog` (quick-create), `pos`,
`inventory` (`expire_batches`), `scripts/`

## Success Criteria

| Criterion | Status |
| --- | --- |
| Documented as-built baseline | Implemented |
| Stock/low-stock use sellable stock logic | Implemented |
| Backup restore requires confirmation | Implemented |
| Dashboard auth separate from Admin login | Implemented |

## Known Gaps

| Gap | Status |
| --- | --- |
| Report CSV/PDF export | Deferred |
| Scheduled `expire_batches` | Deferred — manual command only |

## What Later Versions Should Improve

V3 cost/promotions, V4 roles, V9 report accuracy and owner visibility.
