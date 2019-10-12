from django.contrib import admin

from card.models import Card


class CardAdmin(admin.ModelAdmin):
    model = Card
    list_display = ('__str__', 'user',)
    search_fields = ('number', 'user__username')


admin.site.register(Card, CardAdmin)
