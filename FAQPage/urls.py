from django.contrib.auth.decorators import login_required
from django.urls import path

from contentbox.views import DisplayContentBoxView
from . import views

urlpatterns = [
    path('', views.FAQPageView.as_view(), name='FAQPage'),
    path('3DPrinter', views.PrinterView.as_view(), name='3DPrinterFAQ'),
    # path('symaskiner'),
    # path('loddestasjon'),
]
