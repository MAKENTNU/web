from django.views.generic import TemplateView

from news.models import Article, TimePlace


class IndexView(TemplateView):
    template_name = 'web/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'articles': Article.objects.published().filter(featured=True)[:4],
            'events': TimePlace.objects.published().filter(event__featured=True)[:4],
        })
        return context
