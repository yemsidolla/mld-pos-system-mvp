# Melodu POS Standard Way of Working

This document defines how Melodu POS work must be planned, documented,
implemented, tested, reviewed, and released.

Melodu POS must not grow by random iteration. Every change must follow a
controlled workflow. Documentation is not rewritten every time. The design
system is not changed as a side effect of feature work. The product roadmap is
not changed without decision approval.

## 1. Purpose

The purpose of this document is to keep Melodu POS stable, understandable, and
safe to continue across human developers and AI coding agents.

Every future task must use this standard to decide:

- What type of change is being requested.
- Which documents must be checked first.
- Which files may be touched.
- What approval is required.
- What tests are expected.
- What documentation updates are allowed.
- What must be included in the final handoff.

This standard protects the current product, architecture, documentation, design
system, permissions, deployment model, and roadmap from uncontrolled edits.

## 2. Authority and Decision Ownership

Final product decision owner: Sidolla.

Final technical direction owner: Sidolla.

Implementation: human developers and AI coding agents.

QA/release approval: Sidolla or an assigned reviewer.

Rules:

- AI agents may propose.
- AI agents may inspect.
- AI agents may implement approved scope.
- AI agents must not redefine the product direction.
- AI agents must not silently expand scope.
- AI agents must not rewrite foundation docs unless the task explicitly says so.
- AI agents must treat unclear product, permission, security, data, or roadmap
  decisions as assumptions to be confirmed or clearly marked.

## 3. Document Hierarchy

Melodu POS documentation has different levels of authority. Do not treat every
document as equally editable during normal feature work.

Hierarchy:

1. `README.md`
2. `docs/STANDARD_WAY_OF_WORKING.md`
3. `docs/DESIGN_SYSTEM.md`
4. `docs/versions/` version-specific docs
5. `docs/guides/` operator and developer guides
6. `docs/TASKS.md`
7. `docs/DEVELOPMENT_LOG.md`

Meaning:

- `README.md` is the project entry point. It is not the full product spec.
- `docs/STANDARD_WAY_OF_WORKING.md` defines the process.
- `docs/DESIGN_SYSTEM.md` defines UI/UX rules.
- Version docs define version-specific scope, architecture, and decisions.
- Guides define user-facing, operator-facing, or developer-facing procedures.
- `docs/TASKS.md` tracks implementation work.
- `docs/DEVELOPMENT_LOG.md` records what changed.

Additional handoff document:

- `docs/CURRENT_STATUS.md` describes the current project truth at a point in
  time. It is useful for onboarding and status handoff, but it does not replace
  the process, design system, task tracker, or version docs.

Important rule:

Foundation documents must not be rewritten during normal feature work. They may
only be changed by a dedicated documentation or governance task.

## 4. Change Types

Every task must be classified before implementation starts.

### 1. Bug Fix

Check first:

- `docs/STANDARD_WAY_OF_WORKING.md`
- Relevant guide or version doc.
- Relevant source files and tests.

Files may be touched:

- The broken source path.
- Closely related tests.
- A guide or log only if behavior or operator guidance changes.

Approval required:

- Clear bug report or Sidolla approval.

Tests expected:

- Affected app tests.
- Regression test when practical.

README/design-system/roadmap:

- Do not change unless the bug is in setup, design-system behavior, or roadmap
  text itself.

### 2. UI/UX Polish

Check first:

- `docs/STANDARD_WAY_OF_WORKING.md`
- `docs/DESIGN_SYSTEM.md`
- `/dashboard/styleguide/` if visual components or tokens are involved.
- Relevant templates, CSS, JS, and view tests.

Files may be touched:

- Templates, CSS, small JS, view tests.
- Documentation only if user-facing behavior changes.

Approval required:

- Approved UI polish scope.

Tests expected:

- Relevant view/template tests where available.
- Manual browser check recommended.

README/design-system/roadmap:

- Do not update `docs/DESIGN_SYSTEM.md` unless the task is explicitly a
  design-system task.
- Do not change roadmap.

### 3. Feature Implementation

Check first:

- `docs/STANDARD_WAY_OF_WORKING.md`
- Relevant version/scope docs.
- Relevant module docs and source files.
- Permission and data impact.

Files may be touched:

- Target module code.
- Templates/static files for the feature.
- Tests.
- Task tracker and development log when meaningful.
- Guides if user/operator behavior changes.

Approval required:

- Approved feature scope and acceptance criteria.

Tests expected:

- Affected app tests.
- Integration tests for business workflows.
- Permission tests if access changes.

README/design-system/roadmap:

- Do not update README unless setup, architecture, or major doc links change.
- Do not update design system unless explicitly assigned.
- Do not update roadmap unless Sidolla approves scope change.

### 4. Permission/Auth Change

Check first:

- `docs/STANDARD_WAY_OF_WORKING.md`
- `docs/reference/PERMISSION_MATRIX.md`
- V6 auth/permission docs.
- `core.permissions`, account/auth code, affected views, and tests.

Files may be touched:

- Permission/auth modules.
- Affected view decorators and tests.
- Permission docs and development log.

Approval required:

- Explicit Sidolla approval or assigned auth task.

Tests expected:

- Auth and permission tests.
- No-role/access-denied behavior if relevant.
- Dashboard navigation visibility tests if navigation changes.

README/design-system/roadmap:

- Do not change design system or catalog/POS behavior as a side effect.

### 5. Data Model Change

Check first:

- Relevant model files and migrations.
- Business rules docs.
- Backup/restore and deployment impact.
- Affected services and tests.

Files may be touched:

- Models.
- Migrations.
- Admin/forms/services/views/tests.
- Relevant docs.

Approval required:

- Explicit approval because migrations affect data.

Tests expected:

- `makemigrations --check` before and after as appropriate.
- Migration-aware tests.
- Affected app tests or full suite.

README/design-system/roadmap:

- README only if setup/architecture changes.
- Do not change design system unless UI foundation changes.

### 6. Report Change

Check first:

- Report view/template.
- Business rules for included/excluded records.
- Sales/inventory source data.

Files may be touched:

- Report views/templates/tests.
- Report guide if behavior changes.

Approval required:

- Approved report definition or bug report.

Tests expected:

- Report tests for filters, totals, empty state, and permission.

README/design-system/roadmap:

- Do not change sale creation, inventory logic, README, design system, or
  roadmap unless explicitly required and explained.

### 7. Printing/Label Change

Check first:

- Label/receipt templates.
- Printer/receipt guides.
- Store settings and label template rules.

Files may be touched:

- Label/receipt views/templates/CSS/tests.
- Label or receipt docs.

Approval required:

- Approved print layout or print bug scope.

Tests expected:

- Route rendering tests.
- Print preview/manual print check where possible.

README/design-system/roadmap:

- Do not change unrelated POS or inventory logic.

### 8. Documentation-Only Change

Check first:

- Existing relevant docs.
- `docs/STANDARD_WAY_OF_WORKING.md`.

Files may be touched:

- Requested docs only.
- README only for setup, architecture, or important doc links.

Approval required:

- Documentation/governance request.

Tests expected:

- No app tests required unless setup commands are changed.
- Spell/structure review expected.

README/design-system/roadmap:

- Do not rewrite foundation docs unless explicitly requested.
- Do not invent future behavior unless clearly marked Proposed/Future.

### 9. Design-System Change

Check first:

- `docs/DESIGN_SYSTEM.md`
- `/dashboard/styleguide/`
- Shared CSS/tokens/templates.

Files may be touched:

- Design system docs.
- Styleguide view/template.
- Shared CSS/tokens.
- Tests for rendering/access if affected.

Approval required:

- Dedicated design-system task.

Tests expected:

- Relevant view tests.
- Manual browser/screenshot check when possible.

README/design-system/roadmap:

- Design-system doc may be changed.
- Roadmap only if Sidolla approves product direction change.

### 10. Emergency Production Fix

Check first:

- Immediate failing path.
- Current production deployment docs.
- Rollback options.

Files may be touched:

- Minimum source files needed to stabilize production.
- Tests if time allows.
- Development log and release note after stabilization.

Approval required:

- Sidolla approval, or emergency authorization from assigned operator.

Tests expected:

- Fastest relevant verification.
- Full suite later if not possible immediately.

README/design-system/roadmap:

- Do not broaden scope.
- Do not redesign.
- Do not refactor.

## 5. Standard Work Lifecycle

No implementation should start until the change type and scope are clear.

Required lifecycle:

1. Request.
2. Classification.
3. Scope confirmation.
4. Source inspection.
5. Impact analysis.
6. Task plan.
7. Implementation.
8. Tests.
9. Documentation update, only if required.
10. Development log update, when meaningful.
11. Final summary.
12. Review and release decision.

If the request is small and clear, scope confirmation can be a clearly stated
assumption instead of a blocking question. If the request touches permissions,
data, security, release, destructive actions, or roadmap direction, unclear
scope must be clarified before implementation.

## 6. Definition of Ready

A task is ready only when it has:

- Clear goal.
- Change type.
- Target version or phase.
- Affected module.
- Business reason.
- Files likely affected.
- Permission impact.
- Data impact.
- UI impact.
- Test expectation.
- Acceptance criteria.

If any of these are missing, the agent should ask or make a clearly marked
assumption. High-risk assumptions must be confirmed.

## 7. Definition of Done

A task is done only when:

- Scope was followed.
- No unrelated changes were made.
- Tests were run or the reason for not running is stated.
- Permissions were checked if affected.
- Data migration was checked if models changed.
- UI was checked if templates/CSS changed.
- Documentation was updated only where required.
- `docs/DEVELOPMENT_LOG.md` was updated when the change was meaningful.
- Final summary includes changed files and test result.

## 8. Documentation Update Rules

Documentation must describe the current truth. It must not invent future
behavior unless clearly marked as Proposed/Future.

Rules by document:

`README.md`

- Update only for setup, major architecture, or new important doc links.
- Do not use README as a full product spec.

`docs/STANDARD_WAY_OF_WORKING.md`

- Update only during dedicated governance/process tasks.
- Do not change during normal feature work.

`docs/DESIGN_SYSTEM.md`

- Update only during a dedicated design-system task.
- Do not update during normal feature work.
- Any design-system change must also verify `/dashboard/styleguide/`.

Version docs

- Update only when version scope changes or a version task is completed.
- Do not rewrite past version docs unless correcting factual errors.

`docs/TASKS.md`

- Update when tasks are added, started, completed, blocked, or deferred.

`docs/DEVELOPMENT_LOG.md`

- Update after meaningful implementation or documentation milestones.

Guides

- Update only when user-facing or operator-facing behavior changes.

ADR/decision docs

- Create or update only when a major architecture or product decision is made.

`docs/CURRENT_STATUS.md`

- Update when the actual project state changes meaningfully.
- Keep it factual and current.
- Do not use it as a future roadmap.

## 9. Design System Governance

Rules:

- `docs/DESIGN_SYSTEM.md` is the authoritative design blueprint.
- `/dashboard/styleguide/` is the visual reference.
- CSS, templates, and styleguide must stay aligned.
- No raw colors should be introduced if a token exists.
- No new visual pattern should be introduced without checking the design system.
- Design-system updates require a dedicated task.
- Normal feature work should reuse existing components.

For design-system changes, require:

- Update `docs/DESIGN_SYSTEM.md`.
- Update `/dashboard/styleguide/` if visual components or tokens changed.
- Update CSS/tokens if needed.
- Add or update tests if access or rendering changes.
- Mention screenshots/manual UI check in final summary when possible.

## 10. AI Agent Working Rules

AI agents include Codex, Claude, ChatGPT, Cursor, and similar coding assistants.

The agent must:

- Inspect relevant files before editing.
- Keep scope small.
- Avoid broad rewrites.
- Prefer minimal targeted patches.
- Never change unrelated modules.
- Never rewrite documentation structure without explicit request.
- Never change design system as a side effect.
- Never change permissions/auth as a side effect.
- Never add migrations unless data model change is explicitly required.
- Never delete data/reset scripts without explicit approval.
- Always report tests run.

The agent must not:

- Add new features because they seem useful.
- Rename business terms casually.
- Update roadmap randomly.
- Replace current architecture.
- Convert the monolith to microservices.
- Introduce a new frontend framework.
- Change Authentik/OIDC behavior unless assigned.
- Make destructive reset behavior easier without approval.

## 11. Branch and Commit Rules

Recommended branch naming:

```text
docs/standard-way-of-working
fix/<short-name>
feature/v7-<short-name>
ui/v7-<short-name>
auth/v6-<short-name>
reports/v9-<short-name>
```

Commit style:

```text
Add standard way of working
Fix sale cancellation audit summary
Polish product list empty state
Document V7 UI scope
```

Rules:

- One logical change per commit.
- Do not mix feature, design-system, and docs-governance changes in one commit
  unless explicitly approved.
- Mention tests in final response.

## 12. Testing Rules

Expected test levels:

Documentation-only:

- No app tests required unless README/setup commands are changed.
- Spell/structure review expected.

Backend logic:

- Run Django tests for affected app or full suite.

Permissions/auth:

- Run auth/permission tests.
- Test no-role/access-denied behavior if relevant.

UI/template:

- Run relevant view tests if available.
- Manual browser check recommended.

Data model:

- Generate migrations intentionally.
- Run migrations/check/tests.
- Explain migration impact.

Printing/labels:

- Test preview/print route rendering.
- Manual print check may be required.

Reset/backup:

- Extra caution.
- Must not weaken confirmation/safety behavior.

## 13. Release Rules

Release levels:

Patch release:

- Bug fix or small UI fix.

Minor version:

- Feature group or workflow improvement.

Foundation release:

- Documentation, governance, architecture, or design-system foundation.

Emergency release:

- Production fix only.

Each release summary must include:

- What changed.
- Why it changed.
- Risk level.
- Tests run.
- Rollback note.
- Follow-up tasks.

## 14. Scope Control Rules

Strict rules:

- If the task says "document", do not implement feature behavior.
- If the task says "UI polish", do not change data model.
- If the task says "bug fix", do not redesign the page.
- If the task says "design system", do not change business logic.
- If the task says "auth", do not change unrelated catalog/POS behavior.
- If the task says "report", do not change sale creation logic unless required
  and explained.

## 15. Standard Task Template

Use this template for planning tasks:

```markdown
## Task

**Title:**
**Change Type:**
**Version/Phase:**
**Module:**
**Business Reason:**
**Scope:**
**Out of Scope:**
**Files likely affected:**
**Permission impact:**
**Data impact:**
**UI impact:**
**Docs impact:**
**Acceptance Criteria:**
**Tests Required:**
**Rollback Note:**
```

## 16. Standard Final Response Template for AI Agents

Use this format when finishing a task:

```markdown
## Summary
- ...

## Files Changed
- ...

## Scope Control
- Confirmed in scope:
- Not changed:

## Tests
- ...

## Documentation
- ...

## Risks / Notes
- ...

## Recommended Next Step
- ...
```

## 17. Immediate Rule Going Forward

Before any future Melodu POS task starts, the agent must read:

1. `docs/STANDARD_WAY_OF_WORKING.md`
2. `docs/DESIGN_SYSTEM.md` if UI is affected
3. `docs/product/00_CURRENT_SYSTEM_MAP.md` for current routes, modules, and capabilities
4. The relevant module/version docs
5. The source files directly affected by the task

This rule applies to human developers and AI coding agents.
