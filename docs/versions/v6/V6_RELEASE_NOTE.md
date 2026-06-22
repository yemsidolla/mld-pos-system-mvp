# V6 Release Note Draft

Status: Current
Last updated: 2026-06-16

## Version

V6 Controlled Foundation Reset

## Scope

Documentation and governance only. No application behavior changed.

## Changed

- Added a product-level documentation foundation under `docs/product/`.
- Added V6 reset documents under `docs/versions/v6/`.
- Added ADR-0001 through ADR-0007 under `docs/decisions/`.
- Added a preferred documentation read order and authority map.
- Updated README with compact links to the new documentation map.
- Updated current status to point to the new authoritative maps and remove stale local-change notes.
- Updated the task tracker with controlled foundation reset rows.
- Added a development log milestone for the reset.

## Not Changed

- No Django app code.
- No settings, URLs, templates, CSS, JavaScript, migrations, models, permissions, OIDC behavior, or reset scripts.
- No deployment behavior.
- No data model or database behavior.
- No deletion, rename, archive, or deprecation banner for older docs.

## Docs

Start future work from:

1. `docs/STANDARD_WAY_OF_WORKING.md`
2. `README.md`
3. `docs/CURRENT_STATUS.md`
4. `docs/product/11_DOCUMENTATION_MAP.md`
5. `docs/product/00_CURRENT_SYSTEM_MAP.md`

## Tests

Django tests are not required for this release because the change is Markdown-only. Documentation validation should confirm file structure and git diff.

## Known Risks

| Risk | Status |
| --- | --- |
| Some older docs overlap with the new foundation docs. | Duplicate / Overlapping |
| Production OIDC, scanner, media, printer, and backup behavior still require operational verification. | Needs Verification |
| Future contributors may accidentally use old phase docs as primary authority unless they follow the documentation map. | Needs Verification |

## Rollback

If the reset docs create confusion, revert the documentation commit. No database or runtime rollback is required because no application behavior changes.
