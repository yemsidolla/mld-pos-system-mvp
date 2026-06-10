from django.core.paginator import Paginator

DEFAULT_PAGE_SIZE = 25


def paginate(request, queryset, per_page=DEFAULT_PAGE_SIZE):
    """Return ``(page_obj, querystring)`` for a list view.

    ``querystring`` is the current GET params minus ``page`` (url-encoded), so
    templates can preserve active filters across page links. Pair with the
    shared ``dashboard/_pagination.html`` partial.
    """
    paginator = Paginator(queryset, per_page)
    page_obj = paginator.get_page(request.GET.get("page"))

    params = request.GET.copy()
    params.pop("page", None)
    return page_obj, params.urlencode()
