from django import template


register = template.Library()


@register.filter
def get_item(value, key):
    if not isinstance(value, dict):
        return ""
    item = value.get(key, "")
    return "" if item is None else item
