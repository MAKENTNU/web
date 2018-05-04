from django.urls import re_path

from inventory.views import IndexView

urlpatterns = [
    re_path('(?P<search_word>.*)', IndexView.as_view())
]
