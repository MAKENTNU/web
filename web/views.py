from django.views.generic import TemplateView

from news.models import Article, TimePlace


class IndexView(TemplateView):
    template_name = 'web/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        events = TimePlace.objects.future().filter(event__featured=True)
        if not self.request.user.has_perm('news.can_view_private'):
            events = events.filter(event__private=False)

        context.update({
            'articles': Article.objects.published().filter(featured=True)[:4],
            'events': events[:4],
        })
        return context


class AdminPanelView(TemplateView):
    template_name = 'web/admin_panel.html'


class View404(TemplateView):
    template_name = 'web/404.html'

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context, status=404)

