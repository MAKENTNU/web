from django.contrib import admin

from news.models import Article, Event

admin.site.register(Article)
admin.site.register(Event)
