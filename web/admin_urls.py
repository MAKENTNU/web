from django.conf import settings
from django.contrib import admin
from django.urls import path
from django.views.generic import RedirectView, TemplateView
from django_hosts import reverse


# Updates the "View site" link to this url
admin.site.site_url = f"//{settings.PARENT_HOST}/"

urlpatterns = [
    # Custom paths must come before including `admin.site.urls` to avoid being "hidden" behind Django admin's catch-all path
    path("robots.txt", TemplateView.as_view(template_name='admin/robots.txt', content_type='text/plain')),

    path("", admin.site.urls),
]

# Disable admin page login if Dataporten is configured,
# as in that case, all users would log in through Dataporten anyways
if settings.SOCIAL_AUTH_DATAPORTEN_SECRET:
    urlpatterns.insert(0, path("login/", RedirectView.as_view(
        url=f"{reverse('login', host='main')}?next=//admin.{settings.PARENT_HOST}"
    )))
