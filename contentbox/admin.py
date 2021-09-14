from django.contrib import admin

from web.multilingual.admin import MultiLingualFieldAdmin
from .models import ContentBox


admin.site.register(ContentBox, MultiLingualFieldAdmin)
