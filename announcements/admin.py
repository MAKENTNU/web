from django.contrib import admin

from announcements.models import Announcement
from web.multilingual.database import MultiLingualFieldAdmin

admin.site.register(Announcement, MultiLingualFieldAdmin)
