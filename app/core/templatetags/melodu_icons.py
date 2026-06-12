"""Inline SVG icon set (V7) — no webfont, no external dependency.

24x24 stroke icons in the Tabler outline style. Usage:

    {% load melodu_icons %}
    {% icon "scan" %}            -> 18px icon
    {% icon "scan" 22 "nav-ic" %} -> 22px with extra CSS class
"""
from django import template
from django.utils.html import format_html
from django.utils.safestring import mark_safe

register = template.Library()

ICONS = {
    "home": '<path d="M3 11l9-7 9 7"/><path d="M5 10v10h14V10"/><path d="M10 20v-5h4v5"/>',
    "cart": '<circle cx="9" cy="20" r="1.4"/><circle cx="17" cy="20" r="1.4"/><path d="M3 4h2l2.4 11h10.2L21 8H7"/>',
    "receipt": '<path d="M6 3h12v18l-2-1.5-2 1.5-2-1.5L10 21l-2-1.5L6 21V3z"/><path d="M9 8h6M9 12h6"/>',
    "package": '<path d="M12 3l8 4.5v9L12 21l-8-4.5v-9L12 3z"/><path d="M12 12l8-4.5M12 12v9M12 12L4 7.5"/>',
    "truck": '<rect x="1.5" y="7" width="12" height="8.5" rx="1"/><path d="M13.5 10h3.8l3.2 3v2.5h-7"/><circle cx="6" cy="17.8" r="1.6"/><circle cx="17" cy="17.8" r="1.6"/>',
    "tag": '<path d="M4 4h7.2L20.5 13.3a1.4 1.4 0 010 2L15.3 20.5a1.4 1.4 0 01-2 0L4 11.2V4z"/><circle cx="8" cy="8" r="1"/>',
    "printer": '<path d="M7 8V3h10v5"/><path d="M5 8h14a1.5 1.5 0 011.5 1.5V16H17.5"/><path d="M3.5 16V9.5A1.5 1.5 0 015 8"/><path d="M6.5 16H3.5"/><rect x="6.5" y="13.5" width="11" height="7.5" rx="0.5"/>',
    "chart": '<path d="M4 20V12"/><path d="M10 20V7"/><path d="M16 20v-9"/><path d="M21 20H3"/>',
    "settings": '<circle cx="12" cy="12" r="3"/><path d="M12 2.5v3M12 18.5v3M2.5 12h3M18.5 12h3M5.3 5.3l2.1 2.1M16.6 16.6l2.1 2.1M18.7 5.3l-2.1 2.1M7.4 16.6l-2.1 2.1"/>',
    "shield": '<path d="M12 3l8 3.2v5.6c0 4.4-3.4 7.4-8 9.2-4.6-1.8-8-4.8-8-9.2V6.2L12 3z"/><path d="M9 12l2 2 4-4"/>',
    "activity": '<path d="M3 12h4l3-7 4 14 3-7h4"/>',
    "logs": '<path d="M7 3h8l4 4v14H7V3z"/><path d="M15 3v4h4"/><path d="M10 12h6M10 16h6"/>',
    "user": '<circle cx="12" cy="8" r="3.5"/><path d="M5 21c0-4 3-6 7-6s7 2 7 6"/>',
    "users": '<circle cx="9.5" cy="8.5" r="3"/><path d="M3.5 20c0-3.4 2.6-5 6-5s6 1.6 6 5"/><path d="M15.5 5.8a3 3 0 010 5.4"/><path d="M17.5 15.3c2 .7 3 2.2 3 4.7"/>',
    "scan": '<path d="M4 8V5.5A1.5 1.5 0 015.5 4H8"/><path d="M16 4h2.5A1.5 1.5 0 0120 5.5V8"/><path d="M20 16v2.5a1.5 1.5 0 01-1.5 1.5H16"/><path d="M8 20H5.5A1.5 1.5 0 014 18.5V16"/><path d="M5 12h14"/>',
    "camera": '<rect x="3" y="7" width="18" height="13" rx="2"/><path d="M8.5 7l1.6-2.6h3.8L15.5 7"/><circle cx="12" cy="13.3" r="3.4"/>',
    "cash": '<rect x="3" y="7" width="18" height="11" rx="2"/><circle cx="12" cy="12.5" r="2.6"/><path d="M6.5 10.5v0M17.5 14.5v0"/>',
    "alert": '<path d="M12 4.5L2.8 20h18.4L12 4.5z"/><path d="M12 10.5V14"/><path d="M12 17.2v.1"/>',
    "clock": '<circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3.4 2"/>',
    "logout": '<path d="M13 4H6.5A1.5 1.5 0 005 5.5v13A1.5 1.5 0 006.5 20H13"/><path d="M9.5 12H20"/><path d="M16.5 8l4 4-4 4"/>',
    "upload": '<path d="M12 16V5"/><path d="M7 9.5L12 4.5l5 5"/><path d="M4 19.5h16"/>',
    "percent": '<path d="M5 19L19 5"/><circle cx="7" cy="7" r="2.4"/><circle cx="17" cy="17" r="2.4"/>',
    "barcode": '<path d="M4 6v12M8 6v12M11 6v8M14 6v12M17 6v8M20 6v12"/>',
    "dollar": '<path d="M16 7.8c-.8-1.4-2.2-2.1-4-2.1-2.3 0-4 1.2-4 3s1.6 2.5 4 3 4 1.3 4 3.1-1.7 3-4 3c-1.8 0-3.2-.7-4-2.1"/><path d="M12 3.5v17"/>',
    "search": '<circle cx="10.5" cy="10.5" r="6"/><path d="M15.5 15.5l4.5 4.5"/>',
    "check": '<path d="M5 12.5l4.5 4.5L19 7.5"/>',
    "x": '<path d="M6 6l12 12M18 6L6 18"/>',
    "plus": '<path d="M12 5v14M5 12h14"/>',
    "category": '<rect x="4" y="4" width="6.5" height="6.5" rx="1"/><rect x="13.5" y="4" width="6.5" height="6.5" rx="1"/><rect x="4" y="13.5" width="6.5" height="6.5" rx="1"/><circle cx="16.8" cy="16.8" r="3.2"/>',
    "sidebar": '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M9.5 4v16"/>',
    "trend-up": '<path d="M3 17l6-6 4 4 8-8"/><path d="M15 7h6v6"/>',
}


@register.simple_tag
def icon(name, size=18, css_class=""):
    paths = ICONS.get(name)
    if paths is None:
        return ""
    return format_html(
        '<svg class="icon{}" width="{}" height="{}" viewBox="0 0 24 24" fill="none" '
        'stroke="currentColor" stroke-width="1.8" stroke-linecap="round" '
        'stroke-linejoin="round" aria-hidden="true">{}</svg>',
        f" {css_class}" if css_class else "",
        size,
        size,
        mark_safe(paths),
    )
