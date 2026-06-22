# V10-010 Performance And Database Review

Status: Complete
Last updated: 2026-06-16

## Purpose

Review current database/query readiness before data volume grows, without adding premature migrations or query changes.

## Current Strengths

| Area | Evidence | Status |
| --- | --- | --- |
| Pagination | Shared `core.pagination.paginate()` is used on major list/ledger pages. | Current |
| Stock batch indexes | Product/status, batch number, custom code, and expiry date indexes exist. | Current |
| Inventory movement indexes | Movement type/date and reference indexes exist. | Current |
| Sale indexes | Sale number, cashier/date, and status/date indexes exist. | Current |
| Promotion indexes | Active/date, product/active, category/active indexes exist. | Current |
| Audit indexes | Action/date, module/date, and object type/id indexes exist. | Current |
| Query optimization | Several views use `select_related`, `prefetch_related`, and annotations. | Current |
| Media handling | MinIO/S3-backed storage can reduce large-image transfer pressure when enabled. | Current |

## Risk Areas

| Area | Risk | Status |
| --- | --- | --- |
| Staff sales report | Current aggregation is all-time; it may need date/store filters as data grows. | Needs Verification |
| Promotion report | Aggregates sale-item snapshots; may need date/store filters and pagination for high volume. | Needs Verification |
| Audit log search | Broad search is useful, but text search may slow down with very large audit tables. | Future / Proposed |
| Product images | Large images can affect list/table performance if thumbnails are not optimized. | Needs Verification |
| Stock summary annotations | Product-level stock annotations can grow expensive with many batches. | Needs Verification |
| Multi-store joins | Adding store filters later can add join complexity if not indexed. | Future / Proposed |

## Candidate Future Optimizations

| Candidate | Status | Notes |
| --- | --- | --- |
| Add date filters to staff and promotion reports. | Future / Proposed | Product decision required for default reporting window. |
| Add store/date composite indexes after store fields exist. | Future / Proposed | Do only with migration plan and query evidence. |
| Add audit retention/archive or PostgreSQL full-text search only if needed. | Future / Proposed | Avoid premature complexity. |
| Generate thumbnails for product list images. | Future / Proposed | Useful if real product photos are large. |
| Add performance fixture/load-test plan. | Future / Proposed | Needed before scale release. |

## Baseline Checklist For Future Performance Work

- Record target dataset size: products, batches, sales, sale items, audit rows, media objects.
- Measure page time for POS, product list, stock overview, sales history, audit logs, and reports.
- Use PostgreSQL query plans before adding indexes.
- Add tests that prove optimized queries return the same business results.
- Avoid changing report definitions while optimizing.

## Verification

Review-only. No database indexes, migrations, query behavior, cache layer, or frontend loading behavior changed.

