from django.views.generic import TemplateView

from news.models import Article, Event


class IndexView(TemplateView):
    template_name = 'web/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'articles': Article.objects.filter(event=None),
            'events': Event.objects.all(),
        })
        return context
