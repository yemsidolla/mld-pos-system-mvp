# Product Classification Guide (V4 Phase 2)

Products can be organised for a pet store with two structured fields plus
flexible tags. All classification is **optional** — existing products remain
valid with nothing set.

## Fields

- **Animal type** (single choice): Dog, Cat, Rabbit, Hamster, Bird, Fish, Other.
- **Life stage** (single choice): Baby, Puppy, Kitten, Adult, Senior, All ages.
- **Tags** (`ProductTag`, many): free-form labels you create and reuse, e.g.
  *Grain Free*, *Dental Care*, *Sensitive Skin*, *Small Breed*, *Indoor*, *Snack*,
  *Medicine*, *Toy*. Use tags for everything that is not animal type or life
  stage (usage type, health focus, breed size, age range, …) so you do not have
  to add new structured fields over time.

## Where it appears

- **Product form** (`/dashboard/products/new/` and edit): animal type and life
  stage dropdowns and a multi-select tag picker.
- **Product list** (`/dashboard/products/`): filter by animal type, life stage,
  and tag; the free-text search also matches tag names. Each row shows a
  Classification column with badges.
- **Django Admin**: `Product` gains animal type / life stage / tag filters and a
  tag picker; `ProductTag` has its own admin section.
- **Audit**: product create/update audit entries include the tag list.

## Batch upload

The product upload supports three new **optional** columns:
`animal_type`, `life_stage`, `tags`. Files without them keep working.

- `animal_type` / `life_stage`: use the code values (case-insensitive), e.g.
  `CAT`, `ADULT`. Invalid values are flagged in preview and never committed.
- `tags`: one cell, separated by `;` or `,` (e.g. `Grain Free; Indoor`). Tags
  are created automatically if they do not exist. On update, leaving `tags`
  blank keeps the product's existing tags; a non-empty value replaces them.

Download the current template from the Batch Upload page or see
`docs/batch_upload_templates/products.csv`.

## Notes

- Animal type and life stage are fixed choice lists (stable, common). Extend
  them later only if the store genuinely needs more; prefer tags first.
- Tags are shared across products; rename or deactivate them in Django Admin.
