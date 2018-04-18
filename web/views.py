from django.http import HttpResponse, HttpResponseNotFound
from django.shortcuts import render
from django.template.loader import get_template
from django.views.generic import TemplateView

from news.models import Article, TimePlace


class IndexView(TemplateView):
    template_name = 'web/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'articles': Article.objects.published().filter(featured=True)[:4],
            'events': TimePlace.objects.future().filter(event__featured=True)[:4],
        })
        return context


class AdminPanelView(TemplateView):
    template_name = 'web/admin_panel.html'


