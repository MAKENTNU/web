from django.views.generic import TemplateView

from news.models import Article, Event


class IndexView(TemplateView):
    template_name = 'web/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'articles': Article.objects.published().filter(event=None),
            'events': Event.objects.published(),
        })
        return context
