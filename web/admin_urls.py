from decorator_include import decorator_include
from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.admin.views.decorators import staff_member_required
from django.urls import path
from django.views.generic import RedirectView, TemplateView
from django_hosts import reverse

from util.url_utils import ckeditor_uploader_urls, debug_toolbar_urls, logout_urls


urlpatterns = [
    path("robots.txt", TemplateView.as_view(template_name='admin/robots.txt', content_type='text/plain')),
    path(".well-known/security.txt", TemplateView.as_view(template_name='web/security.txt', content_type='text/plain')),

    *debug_toolbar_urls(),
    path("i18n/", decorator_include(
        staff_member_required,
        'django.conf.urls.i18n'
    )),
    *static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT),  # for development only; Nginx is used in production

    *ckeditor_uploader_urls(),
]
urlpatterns += logout_urls()

urlpatterns += i18n_patterns(
    # Including `admin.site.urls` must be done last, to prevent other paths being "hidden" behind Django admin's catch-all path
    path("", admin.site.urls),

    prefix_default_language=False,
)

# Disable admin page login if Dataporten is configured,
# as in that case, all users would log in through Dataporten anyways
if settings.SOCIAL_AUTH_DATAPORTEN_SECRET:
    urlpatterns.insert(0, path("login/", RedirectView.as_view(
        url=f"{reverse('login', host='main')}?next=//admin.{settings.PARENT_HOST}"
    )))
