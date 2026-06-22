# Melodu POS Documentation

Start here for the `docs/` folder. For process rules, read
`docs/STANDARD_WAY_OF_WORKING.md` first.

## Quick Links

| Need | Start here |
| --- | --- |
| How to work on this repo | `docs/STANDARD_WAY_OF_WORKING.md` |
| Read order and authority | `docs/product/11_DOCUMENTATION_MAP.md` |
| Current project truth | `docs/CURRENT_STATUS.md` |
| UI rules | `docs/DESIGN_SYSTEM.md` |
| Active tasks | `docs/TASKS.md` or `docs/product/09_IMPLEMENTATION_BACKLOG.md` |
| What changed recently | `docs/DEVELOPMENT_LOG.md` |

## Folder Layout

```text
docs/
├── README.md                    # This index
├── STANDARD_WAY_OF_WORKING.md   # Process and governance
├── DESIGN_SYSTEM.md             # UI/UX authority
├── CURRENT_STATUS.md            # Current handoff truth
├── TASKS.md                     # Implementation tracker
├── DEVELOPMENT_LOG.md           # Change history
│
├── product/                     # Foundation docs 00–11 (BRD, PRD, TRD, roadmap)
├── versions/                    # Version scopes, tasks, QA, V6 auth docs
├── decisions/                   # Architecture decision records
├── guides/                      # Operator and developer guides
├── operations/                  # Runbooks and checklists
├── reference/                   # Business rules, permissions, project spec
├── legacy/                      # Historical V2–V5 phase docs
└── batch_upload_templates/      # CSV templates for batch upload
```

## Subfolders

| Folder | Index | Purpose |
| --- | --- | --- |
| `product/` | [README](product/README.md) | Product foundation (BRD, PRD, TRD, roadmap) |
| `versions/` | [README](versions/README.md) | Version delivery docs and V6 auth |
| `decisions/` | [README](decisions/README.md) | ADRs |
| `guides/` | [README](guides/README.md) | How-to guides |
| `operations/` | [README](operations/README.md) | Runbooks and checklists |
| `reference/` | [README](reference/README.md) | Supporting reference docs |
| `legacy/` | [README](legacy/README.md) | Historical V2–V5 phase docs |

## Where New Docs Go

| Document type | Location |
| --- | --- |
| Process or governance change | `docs/STANDARD_WAY_OF_WORKING.md` (dedicated task only) |
| UI/UX rules | `docs/DESIGN_SYSTEM.md` (dedicated task only) |
| Product requirements or roadmap | `docs/product/` |
| Version scope, tasks, QA, release note | `docs/versions/vN/` |
| V6 auth or permission docs | `docs/versions/v6/` |
| Architecture decision | `docs/decisions/ADR-NNNN-short-title.md` |
| Operator or developer procedure | `docs/guides/<TOPIC>_GUIDE.md` |
| Runbook or checklist | `docs/operations/` |
| Business rules or permission reference | `docs/reference/` |
| Historical phase plan (archived) | `docs/legacy/` |
| Active implementation tracking | `docs/TASKS.md` and/or `docs/product/09_IMPLEMENTATION_BACKLOG.md` |
| Meaningful change record | `docs/DEVELOPMENT_LOG.md` |
| Current handoff snapshot | `docs/CURRENT_STATUS.md` |
