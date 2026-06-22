# V4 As-Built Review — User Management, Classification, Printing, and Admin Maintenance

## Summary

V4 delivered five-role staff management, product classification, store/receipt
settings, configurable label templates, promotion labels, and CLI data reset.

## Implemented Features

| Phase | Feature | Status |
| --- | --- | --- |
| 1 | StaffProfile, user CRUD, role matrix gating | Implemented |
| 2 | Tags, animal type, life stage on products | Implemented |
| 3 | StoreSetting, thermal receipt, reprint audit | Implemented |
| 4 | LabelTemplate, product label print | Implemented |
| 5 | Promotion label print page | Implemented |
| 6 | `reset_business_data` with dry-run and guards | Implemented |

## Partially Implemented Features

| Feature | Status |
| --- | --- |
| Data-driven capability editor | Evolved in V6 — Partially Implemented at V4 end |

## Permissions Impact

Moved from Admin/Cashier-only to five roles. Cashier still POS-focused; Viewer
read-only reports/history.

## Safety Controls (Reset)

- Dry-run default
- `ALLOW_DATA_RESET=1` env guard
- Exact phrase confirmation
- `--backup-confirmed` flag
- Never deletes users, settings, templates, audit logs

## Handoff to Next Version

V5 — dashboard polish, audit log page, list consistency, mobile slice.
