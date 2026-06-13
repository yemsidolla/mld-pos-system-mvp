"""Helpers for the column-filter list-page pattern (DESIGN_SYSTEM §4.14–4.15).

Reused across list pages as they migrate to the column-header filter pattern.
"""


def querystring_without(request, *drop):
    """Current GET querystring minus ``page`` and any ``drop`` params.

    Returns a ready-to-use href for active-filter "remove" chips and "Clear all"
    so a click drops that column's filter while preserving the others.
    """
    params = request.GET.copy()
    params.pop("page", None)
    for key in drop:
        params.pop(key, None)
    encoded = params.urlencode()
    return f"{request.path}?{encoded}" if encoded else request.path
