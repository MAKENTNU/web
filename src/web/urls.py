from decorator_include import decorator_include
from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.urls import include, path, re_path
from django.views import defaults
from django.views.generic import TemplateView
from django.views.generic.base import RedirectView
from django.views.i18n import JavaScriptCatalog
from social_core.utils import setting_name

from announcements import urls as announcements_urls
from checkin import urls as checkin_urls
from contentbox.views import ContentBoxDetailView, ContentBoxUpdateView
from dataporten.views import login_wrapper
from faq import urls as faq_urls
from groups import urls as groups_urls
from make_queue import urls as make_queue_urls
from make_queue.forms.reservation import ReservationListQueryForm
from makerspace import urls as makerspace_urls
from news import urls as news_urls
from users import urls as users_urls
from util.url_utils import (
    ckeditor_uploader_urls,
    debug_toolbar_urls,
    logout_urls,
    permission_required_else_denied,
)
from util.view_utils import RedirectViewWithStaticQuery
from . import views


extra = "/" if getattr(settings, setting_name("TRAILING_SLASH"), True) else ""

urlpatterns = [
    path(
        "robots.txt",
        TemplateView.as_view(template_name="web/robots.txt", content_type="text/plain"),
    ),
    path(
        ".well-known/security.txt",
        TemplateView.as_view(
            template_name="web/security.txt", content_type="text/plain"
        ),
    ),
    *debug_toolbar_urls(),
    path("i18n/", include("django.conf.urls.i18n")),
    # For development only; Nginx is used in production
    *static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT),
    *ckeditor_uploader_urls(),
]

admin_urlpatterns = [
    path("", views.AdminPanelView.as_view(), name="admin_panel"),
    # App paths, sorted by app label (should have the same path prefixes as the ones in `urlpatterns` below):
    path("announcements/", include(announcements_urls.adminpatterns)),
    path("checkin/", include(checkin_urls.adminpatterns)),
    path("faq/", include(faq_urls.adminpatterns)),
    path("committees/", include(groups_urls.adminpatterns)),
    path("reservation/", include(make_queue_urls.adminpatterns)),
    path("makerspace/", include(makerspace_urls.adminpatterns)),
    path("news/", include(news_urls.adminpatterns)),
]

admin_api_urlpatterns = [
    # App paths, sorted by app label (should have the same path prefixes as the ones in `urlpatterns` below):
    path("checkin/", include(checkin_urls.adminapipatterns)),
    path("news/", include(news_urls.adminapipatterns)),
    path("users/", include(users_urls.adminapipatterns)),
]

api_urlpatterns = [
    # This internal permission is only used for base-level access control;
    # each included path/view should implement its own supplementary access control
    path(
        "admin/",
        decorator_include(
            permission_required_else_denied("internal.is_internal"),
            admin_api_urlpatterns,
        ),
    ),
    # App paths, sorted by app label (should have the same path prefixes as the ones in `urlpatterns` below):
    path("reservation/", include(make_queue_urls.apipatterns)),
]

content_box_urlpatterns = [
    path(
        "<int:pk>/change/",
        ContentBoxUpdateView.as_view(base_template="web/base.html"),
        name="content_box_update",
    ),
]

about_urlpatterns = [
    path("", views.AboutUsView.as_view(url_name="about"), name="about"),
    ContentBoxDetailView.get_path("contact"),
]

urlpatterns += i18n_patterns(
    path("", views.IndexPageView.as_view(), name="index_page"),
    # This internal permission is only used for base-level access control;
    # each included path/view should implement its own supplementary access control
    path(
        "admin/",
        decorator_include(
            permission_required_else_denied("internal.is_internal"), admin_urlpatterns
        ),
    ),
    path("api/", include(api_urlpatterns)),
    # App paths, sorted by app label:
    path("announcements/", include("announcements.urls")),
    path("checkin/", include("checkin.urls")),
    path("faq/", include("faq.urls")),
    path("committees/", include("groups.urls")),
    path("reservation/", include("make_queue.urls")),
    path("makerspace/", include("makerspace.urls")),
    path("news/", include("news.urls")),
    # ContentBox paths:
    path("contentbox/", include(content_box_urlpatterns)),
    path("about/", include(about_urlpatterns)),
    *ContentBoxDetailView.get_multi_path("apply", "søk", "sok"),
    ContentBoxDetailView.get_path("cookies"),
    ContentBoxDetailView.get_path("privacypolicy"),
    # This path must be wrapped by `i18n_patterns()`
    # (see https://docs.djangoproject.com/en/stable/topics/i18n/translation/#django.views.i18n.JavaScriptCatalog)
    path("jsi18n/", JavaScriptCatalog.as_view(), name="javascript_catalog"),
    prefix_default_language=False,
)

# Configure login based on if we have configured Dataporten or not.
if settings.USE_DATAPORTEN_AUTH:
    urlpatterns += i18n_patterns(
        path(
            "login/",
            RedirectView.as_view(url="/login/dataporten/", query_string=True),
            name="login",
        ),
        # This line must come before including `social_django.urls` below, to override social_django's `complete` view
        re_path(rf"^complete/(?P<backend>[^/]+){extra}$", login_wrapper),
        path("", include("social_django.urls", namespace="social")),
        prefix_default_language=False,
    )
else:
    # If it is not configured, we would like to have a simple login page. So that
    # we can test with non-superusers without giving them access to the admin page.
    urlpatterns += i18n_patterns(
        path(
            "login/",
            auth_views.LoginView.as_view(
                template_name="web/login.html",
                redirect_authenticated_user=True,
                # This allows the `next` query parameter (used when logging in) to redirect to pages on all the subdomains
                success_url_allowed_hosts=set(settings.ALLOWED_REDIRECT_HOSTS),
            ),
            name="login",
        ),
        prefix_default_language=False,
    )
urlpatterns += logout_urls()

Owner = ReservationListQueryForm.Owner
# --- Old URLs ---
# URLs kept for "backward-compatibility" after paths were changed, so that users are simply redirected to the new URLs.
# These need only be URLs for pages that are likely to have been linked to, and that are deemed important to keep working.
urlpatterns += i18n_patterns(
    path("rules/", RedirectView.as_view(pattern_name="rules", permanent=True)),
    path(
        "reservation/",
        RedirectView.as_view(pattern_name="machine_list", permanent=True),
    ),
    path(
        "reservation/<int:year>/<int:week>/<int:pk>/",
        RedirectView.as_view(
            url="/reservation/machines/%(pk)s/?calendar_year=%(year)s&calendar_week=%(week)s",
            permanent=True,
        ),
    ),
    path(
        "reservation/me/",
        RedirectViewWithStaticQuery.as_view(
            pattern_name="reservation_list", query={"owner": Owner.ME}, permanent=True
        ),
    ),
    path(
        "reservation/admin/",
        RedirectViewWithStaticQuery.as_view(
            pattern_name="reservation_list", query={"owner": Owner.MAKE}, permanent=True
        ),
    ),
    path(
        "reservation/slots/",
        RedirectView.as_view(
            pattern_name="reservation_find_free_slots", permanent=True
        ),
    ),
    path(
        "reservation/rules/<int:pk>/",
        RedirectView.as_view(pattern_name="reservation_rule_list", permanent=True),
    ),
    path(
        "reservation/machinetypes/<int:pk>/rules/",
        RedirectView.as_view(pattern_name="reservation_rule_list", permanent=True),
    ),
    path(
        "reservation/rules/usage/<int:pk>/",
        RedirectView.as_view(pattern_name="machine_usage_rule_detail", permanent=True),
    ),
    path(
        "reservation/machinetypes/<int:pk>/rules/usage/",
        RedirectView.as_view(pattern_name="machine_usage_rule_detail", permanent=True),
    ),
    path(
        "news/article/<int:pk>/",
        RedirectView.as_view(pattern_name="article_detail", permanent=True),
    ),
    path(
        "news/event/<int:pk>/",
        RedirectView.as_view(pattern_name="event_detail", permanent=True),
    ),
    path(
        "news/ticket/<uuid:pk>/",
        RedirectView.as_view(pattern_name="event_ticket_detail", permanent=True),
    ),
    path(
        "news/ticket/me/",
        RedirectView.as_view(pattern_name="event_ticket_my_list", permanent=True),
    ),
    prefix_default_language=False,
)


# These handlers are automatically registered by Django
# (see https://docs.djangoproject.com/en/stable/topics/http/views/#customizing-error-views)


def handler404(request, exception):
    return defaults.page_not_found(
        request, exception=exception, template_name="web/404.html"
    )


def handler500(request):
    return defaults.server_error(request, template_name="web/500.html")
