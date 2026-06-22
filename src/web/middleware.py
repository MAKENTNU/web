from http import HTTPStatus

from django.conf import settings
from django.db.models import F

from web.models import PageView, Visitor

IGNORED_PREFIXES = (
    "/static/",
    "/media/",
    "/admin/jsi18n",
    "/jsi18n/",
    "/__debug__/",
    "/favicon",
    "/api/",
    "/i18n/",
)


def _visitor_identifier(request):
    if getattr(request, "user", None) and request.user.is_authenticated:
        return f"u:{request.user.pk}"
    if not request.session.session_key:
        request.session.save()
    return f"s:{request.session.session_key}"


def _strip_language_prefix(path):
    """Strips a leading ``/<lang>/`` segment so traffic aggregates per page."""
    for code, _name in settings.LANGUAGES:
        prefix = f"/{code}/"
        if path.startswith(prefix):
            return "/" + path[len(prefix) :]
        if path == f"/{code}":
            return "/"
    return path


class PageViewMiddleware:
    """Records a page view per successful ``GET`` request and tracks the visitor."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.method == "GET" and response.status_code == HTTPStatus.OK:
            path = _strip_language_prefix(request.path)
            if not any(path.startswith(p) for p in IGNORED_PREFIXES):
                obj, _created = PageView.objects.get_or_create(path=path)
                PageView.objects.filter(pk=obj.pk).update(count=F("count") + 1)

                identifier = _visitor_identifier(request)
                Visitor.objects.update_or_create(identifier=identifier)
        return response
