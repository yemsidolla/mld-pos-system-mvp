# Team Governance And Delivery Rules

Status: Implemented (documentation)
Last updated: 2026-06-17

This document aligns product delivery governance with `docs/STANDARD_WAY_OF_WORKING.md`.
It does not replace the standard; it summarizes how Melodu POS work is owned and delivered.

## Governance Model

| Role | Responsibility | Status |
| --- | --- | --- |
| Owner / product decision | Sidolla | Implemented |
| Business input | Shop owner / staff feedback | Implemented |
| Product planning | Sidolla + planning tools | Implemented |
| Technical review | Backend engineer / AI coding tool | Implemented |
| Implementation | Human developer + AI agents | Implemented |
| QA | Sidolla or assigned tester | Implemented |
| Release approval | Sidolla | Implemented |

## Who Does What

| Activity | Owner | Notes |
| --- | --- | --- |
| Request features or fixes | Sidolla / shop staff | Must include business reason |
| Approve scope | Sidolla | Required before implementation |
| Write BRD content | Sidolla / product planner | `docs/product/05_BRD.md` |
| Write PRD content | Sidolla / product planner | `docs/product/06_PRD.md` |
| Write TRD content | Sidolla / technical reviewer | `docs/product/07_TRD.md` |
| Implement code | Developer + AI | Only approved scope |
| Test | Sidolla / assigned tester | Per `docs/product/10_QA_RELEASE_PROCESS.md` |
| Approve release | Sidolla | After QA gates pass |

## Core Rule

No coding starts unless the task has:

- Clear business reason
- Product requirement or bug report
- Technical scope note
- Acceptance criteria
- Change type from `docs/STANDARD_WAY_OF_WORKING.md`

## Definition Of Ready

A task is ready when it has:

| Field | Required |
| --- | --- |
| Title | Yes |
| Change type | Yes |
| Target version or phase | Yes |
| Affected module | Yes |
| Business reason | Yes |
| Scope | Yes |
| Out of scope | Yes |
| Files likely affected | Yes |
| Permission impact | Yes |
| Data impact | Yes |
| UI impact | Yes |
| Docs impact | Yes |
| Acceptance criteria | Yes |
| Tests required | Yes |
| Rollback note | For risky changes |

Use the task template in `docs/STANDARD_WAY_OF_WORKING.md` §15.

## Definition Of Done

A task is done when:

- Scope was followed
- No unrelated changes were made
- Tests were run or reason stated
- Permissions checked if affected
- Migrations checked if models changed
- UI checked if templates/CSS changed
- Documentation updated only where required
- `docs/DEVELOPMENT_LOG.md` updated for meaningful changes
- Final summary includes changed files and test result

## Change Control

| Rule | Status |
| --- | --- |
| Foundation docs change only in dedicated governance tasks | Implemented |
| Roadmap changes need Sidolla approval | Implemented |
| Design-system changes need dedicated design-system task | Implemented |
| Permission/auth changes need explicit approval | Implemented |
| Data model changes need explicit approval | Implemented |
| AI agents propose and implement; they do not redefine product direction | Implemented |

## Version Freeze Rules

| Version | Rule |
| --- | --- |
| V6 | Foundation reset and access documentation — no heavy UI coding in scope |
| V7 | UX/UI polish only — no business logic, auth, or schema changes |
| V8 | Inventory/label/promotion professionalization within current architecture |
| V9 | Reports/audit/owner control within current architecture |
| V10 | Scale-readiness planning — no full multi-store implementation without separate approval |

## Emergency Fix Rules

Production emergencies:

- Touch minimum source files to stabilize
- Fastest relevant verification first
- Full test suite later if not possible immediately
- Development log and release note after stabilization
- No scope broadening, redesign, or refactor

## AI Coding Agent Workflow

1. Read `docs/STANDARD_WAY_OF_WORKING.md`
2. Read `docs/product/00_CURRENT_SYSTEM_MAP.md`
3. Read relevant product/version docs and source files
4. Classify change type
5. Confirm or state assumptions for unclear scope
6. Implement smallest safe change
7. Run tests or state why not
8. Update docs only where required
9. Use final response template from SWOW §16

## Human Review Workflow

1. Review scope against version doc and backlog item
2. Review git diff for unrelated changes
3. Run or verify test evidence
4. Manual UI check for template/CSS work
5. Permission check for auth/navigation changes
6. Approve, request changes, or defer
