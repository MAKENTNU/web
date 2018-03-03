from django.contrib import admin

from news.models import Article, Event, TimePlace

admin.site.register(Article)
admin.site.register(Event)
admin.site.register(TimePlace)
