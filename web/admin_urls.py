from django.contrib import admin
from django.urls import path
from django.views.generic import RedirectView, TemplateView
from django_hosts import reverse

from web import settings

# Updates the "View site" link to this url
admin.site.site_url = f"//{settings.PARENT_HOST}/"

urlpatterns = [
    path('robots.txt', TemplateView.as_view(template_name='web/admin_robots.txt', content_type='text/plain')),
    path('', admin.site.urls),
]

# Disable admin page login if Dataporten is configured. In this
# case, all users would log in through Dataporten anyways, so
# there would be no passwords to login through the admin page login.
if settings.SOCIAL_AUTH_DATAPORTEN_SECRET:
    urlpatterns.insert(0, path('login/', RedirectView.as_view(
        url=f"{reverse('login', host='main')}?next=//admin.{settings.PARENT_HOST}"
    )))
