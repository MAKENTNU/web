from django.contrib import admin
from django.urls import path
from web import settings

# Updates the "View site" link to this url
admin.site.site_url = f"//{settings.PARENT_HOST}/"

urlpatterns = [
    path('', admin.site.urls),
]
