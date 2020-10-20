from django.shortcuts import render
from django.views.generic import DetailView, ListView
from contentbox.views import DisplayContentBoxView
from django.http import HttpResponse
# Create your views here.
from faq.models import Question


class FAQPageView(ListView):
    template_name = 'FAQPage/MainPage/FAQ.html'
    queryset = Question.objects.all()
    context_object_name = 'questions'

