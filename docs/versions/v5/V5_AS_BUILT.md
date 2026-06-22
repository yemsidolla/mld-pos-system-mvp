# V5 As-Built Review — UI/UX Polish, Naming Cleanup, and Product Usability

## Summary

V5 delivered six polish phases: role-aware home, audit log page, paginated
lists, workflow shortcuts, shared list patterns, and a mobile/visual slice.

## Implemented Features

| Feature | Status |
| --- | --- |
| Dashboard home respects capabilities (no POS dead-end) | Implemented |
| Renames: Reference Costs, Receive Stock, Stock Overview, System Health | Implemented |
| `/dashboard/audit-logs/` read-only with filters | Implemented |
| Pagination on long lists | Implemented |
| Stock-in → print barcode shortcut | Implemented |
| Shared filter/pagination patterns | Implemented |
| Mobile nav and table scroll improvements (slice) | Partially Implemented |

## Deferred

- Full label print consolidation (two entry points kept)
- Full stacked-card table redesign on mobile

## Documentation Impact

`docs/legacy/V5_*` plans; design-system preparation informed ADR-0006 and V7.

## Known Risks

| Risk | Notes |
| --- | --- |
| Wording changes may need EN/KH review | Carried to V7-011 |
| UI polish without design-system task | V7 must follow DESIGN_SYSTEM.md |

## Handoff to Next Version

V6 — documentation foundation, OIDC docs, capability matrix formalization.
V7 — continue UI cleanup V5 did not finish.
