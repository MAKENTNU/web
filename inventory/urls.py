from django.urls import re_path

from inventory.views import InventoryView

urlpatterns = [
    re_path('(?P<search_word>.*)', InventoryView.as_view())
]
