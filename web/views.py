from django.contrib.auth.mixins import UserPassesTestMixin
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


class AdminPanelView(UserPassesTestMixin, TemplateView):
    template_name = 'web/admin_panel.html'
    possible_permissions = [
        "news.add_article", "news.change_article", "news.delete_article",
        "news.add_event", "news.change_event", "news.delete_event",
        "news.add_timeplace", "news.change_timeplace", "news.delete_timeplace",
        "make_queue.can_create_event_reservation",
        "make_queue.change_quota",
        "make_queue.change_printer3dcourse",
        "groups.can_edit_group",
    ]

    def test_func(self):
        return any(self.request.user.has_perm(permission) for permission in self.possible_permissions)


class View404(TemplateView):
    template_name = 'web/404.html'

    def get(self, request, *args, **kwargs):
        return self.render_to_response({}, status=404)


class View500(TemplateView):
    template_name = "web/500.html"

    def get(self, request, *args, **kwargs):
        return self.render_to_response({}, status=500)
