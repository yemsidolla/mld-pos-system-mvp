# V7 Scope: UX/UI Cleanup & Staff Workflow Polish

Status: Complete
Last updated: 2026-06-16

## 1. Version Name

V7 - UX/UI Cleanup & Staff Workflow Polish

## 2. Status

Complete. V7 was implemented task-by-task and closed by V7-012 QA/release preparation.

## 3. Goal

Make the existing dashboard cleaner, friendlier, faster, and easier for real shop staff to use without introducing major new business features.

## 4. Business Reason

The system already has many workflows. V7 should reduce confusion, improve consistency, and make the product feel calmer and more professional for daily staff use.

## 5. Current Source Assumptions

| Source | Assumption | Status |
| --- | --- | --- |
| `docs/DESIGN_SYSTEM.md` | The dashboard design system is authoritative and unchanged. | Current |
| `docs/product/00_CURRENT_SYSTEM_MAP.md` | Current routes/modules are the source for V7 screen inventory. | Current |
| `app/templates/dashboard/base.html` | Shared dashboard shell is already in place. | Current |
| `app/core/static/core/css/dashboard.css` | Shared tokens/components already exist. | Current |
| Role/capability helpers | Navigation and page access are capability-aware. | Current |
| Mobile scanner and phone UX | Must be checked on real devices. | Needs Verification |

## 6. In Scope

- Navigation cleanup and menu grouping review.
- Page title and naming consistency.
- Dashboard home polish.
- POS cashier workflow polish.
- Catalog/product list polish.
- Inventory and stock receiving workflow polish.
- Promotion, label, and printing page polish.
- Reports page readability polish.
- Audit, log, and system page polish.
- Empty states, error states, and access-denied/no-role pages.
- Form, table, search, filter, and action consistency.
- Role-aware visibility review.
- Mobile/tablet usability review.
- English/Khmer wording consistency review.

## 7. Out Of Scope

- New inventory logic.
- New POS payment features.
- New promotion engine logic.
- New report calculations.
- New database models or migrations.
- New Authentik/OIDC behavior.
- New permissions or global role model.
- New multi-store behavior.
- Major design-system rewrite.
- Replacing Django templates or the dashboard architecture.

## 8. Dependencies

- `docs/STANDARD_WAY_OF_WORKING.md`
- `docs/DESIGN_SYSTEM.md`
- V6 foundation/current-system docs.
- Current dashboard templates, CSS tokens, route map, and permission system.

## 9. Risks

| Risk | Mitigation |
| --- | --- |
| UI polish accidentally changes business behavior. | Keep changes to templates/CSS/small JS and run view/workflow tests. |
| Role-aware navigation exposes wrong actions. | Test Owner, Manager, Inventory, Cashier, Viewer, and no-role cases. |
| Mobile changes break desktop density. | Verify both desktop and phone/tablet widths. |
| Wording changes confuse existing staff. | Keep business terms consistent and review English/Khmer labels. |

## 10. Success Criteria

- Staff can understand where to go without training.
- Cashier POS flow feels faster and cleaner.
- Pages use consistent titles, actions, buttons, filters, tables, and empty states.
- No role sees unrelated actions.
- No application behavior changes unexpectedly.
- Design system is followed.

## 11. Task Groups

- V7-001 Navigation and naming cleanup audit.
- V7-002 Dashboard home polish.
- V7-003 POS cashier workflow polish.
- V7-004 Catalog/product list polish.
- V7-005 Inventory and stock receiving workflow polish.
- V7-006 Promotion and label page polish.
- V7-007 Reports page readability polish.
- V7-008 Audit/log/system pages polish.
- V7-009 Empty/error/access-denied states polish.
- V7-010 Mobile/tablet usability pass.
- V7-011 English/Khmer wording consistency review.
- V7-012 V7 QA and release preparation.

## 12. Testing Focus

- Template rendering and navigation visibility.
- Role-specific dashboard access.
- POS smoke flow without data-model changes.
- Mobile/desktop browser checks.
- No migration check if implementation remains UI-only.

## 13. Release Criteria

- All approved V7 tasks marked `Complete` in `docs/versions/VERSION_COMPLETION_TRACKER.md`.
- Relevant tests run and documented.
- Manual UI checks recorded.
- `docs/DEVELOPMENT_LOG.md` updated.
- V7 release note finalized from `V7_RELEASE_NOTE.md`.

## 14. Handoff Notes

V7 should be implemented task-by-task. Do not bundle unrelated UI rewrites, and do not edit `docs/DESIGN_SYSTEM.md` unless Sidolla approves a dedicated design-system task.
