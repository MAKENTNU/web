from django.contrib import admin

from card.models import Card


class CardAdmin(admin.ModelAdmin):
    model = Card
    list_display = ('number', 'user',)


admin.site.register(Card, CardAdmin)
