from django.contrib import admin

from contentbox.models import ContentBox
from web.multilingual.admin import MultiLingualFieldAdmin

admin.site.register(ContentBox, MultiLingualFieldAdmin)
