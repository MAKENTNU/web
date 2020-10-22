from django.shortcuts import render
from django.views.generic import DetailView, ListView
from contentbox.views import DisplayContentBoxView
from django.http import HttpResponse
# Create your views here.
from faq.models import Question, Category


class FAQPageView(ListView):
    template_name = 'faq/faqlist.html'
    context_object_name = 'categories'

    def get_queryset(self):
        return Category.objects.prefetch_related('questions')

