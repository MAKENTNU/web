from django.shortcuts import render
from django.views.generic import DetailView
from contentbox.views import DisplayContentBoxView
from django.http import HttpResponse
# Create your views here.


class FAQPageView(DisplayContentBoxView):
    template_name = 'FAQPage/MainPage/FAQ.html'
    title = 'FAQPage'


class PrinterView(DisplayContentBoxView):
    template_name = 'FAQPage/3DPrinter/3dprinter.html'
    title = 'FAQPage'

