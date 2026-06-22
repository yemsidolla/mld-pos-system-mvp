# V8 Label Template Management Polish

Status: Complete
Last updated: 2026-06-16

## Scope

V8-006 improved label template list/form clarity without adding a drag-and-drop designer, changing migrations, or deleting/overwriting existing templates.

## Changes

| Area | Change | Status |
| --- | --- | --- |
| Template list | Added template/default/inactive metrics. | Current |
| Template table | Added orientation/font and enabled field summary. | Current |
| Template model | Added `enabled_field_labels` property for display only. | Current |
| Template form | Grouped fields into identity, paper/text, fields, custom text, and default/status sections. | Current |
| Help text | Added paper size, orientation, font, barcode, QR, default, and active guidance. | Current |
| Guide | Updated `docs/guides/LABEL_TEMPLATE_GUIDE.md`. | Current |

## Rules Preserved

- Only one default template is kept per template type.
- Inactive templates remain saved but are not selectable for printing.
- No existing template is deleted or overwritten by the form.
- Template management remains catalog/manager gated.

## Validation

Command:

```bash
docker compose run --rm --no-deps -v "$PWD/app:/app" web python manage.py test labels.tests --noinput --verbosity 2
```

Result: 13 tests passed.

## Notes

Physical printer verification remains required before a new default template is used in production.
