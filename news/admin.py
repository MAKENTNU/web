from django.contrib import admin

from web.multilingual.admin import MultiLingualFieldAdmin
from .models import Article, Event, EventTicket, TimePlace

admin.site.register(Article, MultiLingualFieldAdmin)
admin.site.register(Event, MultiLingualFieldAdmin)
admin.site.register(TimePlace)
admin.site.register(EventTicket)
