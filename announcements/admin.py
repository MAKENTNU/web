from django.contrib import admin

from web.multilingual.database import MultiLingualFieldAdmin
from .models import Announcement

admin.site.register(Announcement, MultiLingualFieldAdmin)
