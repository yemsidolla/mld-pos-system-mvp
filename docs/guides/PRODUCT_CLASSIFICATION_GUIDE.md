# Product Classification Guide (V4 Phase 2)

Products can be organised for a pet store with structured fields plus
flexible tags. All classification is **optional** — existing products remain
valid with nothing set.

## Fields

- **Animal types** (multiple choice): reusable species options such as Dog,
  Cat, Rabbit, Hamster, Bird, Fish, and Other. Admin users can create more
  animal types when the store genuinely needs them.
- **Life stage** (single choice): Baby, Puppy, Kitten, Adult, Senior, All ages.
- **Tags** (`ProductTag`, many): free-form labels you create and reuse, e.g.
  *Grain Free*, *Dental Care*, *Sensitive Skin*, *Small Breed*, *Indoor*, *Snack*,
  *Medicine*, *Toy*. Use tags for everything that is not animal type or life
  stage (usage type, health focus, breed size, age range, …) so you do not have
  to add new structured fields over time.

## Where it appears

- **Product form** (`/dashboard/products/new/` and edit): multi-select animal
  type checkboxes, a life stage dropdown, and a multi-select tag picker. The
  form includes a **New animal type** quick-add button for creating an option
  without leaving unsaved product data.
- **Product list** (`/dashboard/products/`): filter by animal type, life stage,
  and tag; the free-text search also matches tag names. Each row shows a
  Classification column with badges.
- **Animal Types** (`/dashboard/animal-types/`): Admin users can create, edit,
  activate, or deactivate reusable animal type options. Leave the code blank on
  create to generate it from the name, e.g. `Reptile` becomes `REPTILE`.
- **Django Admin**: `Product` gains animal type / life stage / tag filters plus
  animal type and tag pickers; `AnimalTypeOption` and `ProductTag` have their
  own admin sections.
- **Audit**: product create/update audit entries include the tag list.

## Batch upload

The product upload supports three new **optional** columns:
`animal_type`, `life_stage`, `tags`. Files without them keep working.

- `animal_type`: use one or more code values (case-insensitive), separated by
  `;` or `,`, e.g. `CAT; DOG`. Codes must match active Animal Types from the
  dashboard. Invalid values are flagged in preview and never committed.
- `life_stage`: use one code value (case-insensitive), e.g. `ADULT`.
- `tags`: one cell, separated by `;` or `,` (e.g. `Grain Free; Indoor`). Tags
  are created automatically if they do not exist. On update, leaving `tags`
  blank keeps the product's existing tags; a non-empty value replaces them.

Download the current template from the Batch Upload page or see
`docs/batch_upload_templates/products.csv`.

## Notes

- Animal types are seeded as reusable options from the starting pet list. Add
  more only for species or animal groups; prefer tags for product qualities that
  are not species.
- Tags are shared across products; rename or deactivate them in Django Admin.
