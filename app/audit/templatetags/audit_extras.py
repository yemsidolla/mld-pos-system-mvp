"""Template helpers for rendering audit log value diffs."""
from django import template

register = template.Library()


@register.filter
def change_rows(log):
    """Merge old_value/new_value JSON into per-key before→after rows."""
    old = log.old_value if isinstance(log.old_value, dict) else None
    new = log.new_value if isinstance(log.new_value, dict) else None
    if old is None and new is None:
        return []
    old = old or {}
    new = new or {}
    rows = []
    for key in sorted(set(old) | set(new)):
        before = old.get(key, "")
        after = new.get(key, "")
        rows.append(
            {
                "key": key,
                "before": before,
                "after": after,
                "changed": key in old and key in new and before != after,
            }
        )
    return rows
