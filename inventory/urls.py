from django.urls import re_path, path

from inventory.views import InventoryView, SearchItemsView

urlpatterns = [
    path('', InventoryView.as_view(), name='inventory'),
    path('search', SearchItemsView.as_view(), name='search'),
]
