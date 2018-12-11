from django.contrib import admin

from news.models import Article, Event, TimePlace
from web.multilingual.database import MultiLingualFieldAdmin

admin.site.register(Article, MultiLingualFieldAdmin)
admin.site.register(Event, MultiLingualFieldAdmin)
admin.site.register(TimePlace)
