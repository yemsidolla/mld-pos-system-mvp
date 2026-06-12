"""POS display helpers."""
from decimal import Decimal

from django import template

register = template.Library()


@register.filter
def khr(amount, rate):
    """USD → KHR display amount, rounded to the nearest 100 riel."""
    try:
        riel = Decimal(str(amount)) * Decimal(str(rate or 0))
    except Exception:
        return ""
    rounded = int((riel / 100).quantize(Decimal("1"))) * 100
    return f"{rounded:,}"
