from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import render
from django.views.generic import TemplateView

from contentbox.views import DisplayContentBoxView
from news.models import Article, Event


class IndexView(TemplateView):
    MAX_EVENTS_SHOWN = 4
    MAX_ARTICLES_SHOWN = 4

    template_name = 'web/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        event_dicts = []
        for event in Event.objects.filter(hidden=False):
            if event.private and not self.request.user.has_perm('news.can_view_private'):
                continue
            if not event.get_future_occurrences().exists():
                continue
            if event.standalone:
                event_dicts.append({
                    'first_occurrence': event.get_future_occurrences().first(),
                    'event': event,
                    'number_of_occurrences': event.timeplaces.count(),
                })
            else:
                event_dicts.append({
                    'first_occurrence': event.get_future_occurrences().first(),
                    'event': event,
                    'number_of_occurrences': event.get_future_occurrences().count(),
                })

        sorted_event_dicts = sorted(event_dicts, key=lambda event: event['first_occurrence'].start_time)
        articles = Article.objects.published().visible_to(self.request.user).filter(featured=True)
        context.update({
            'event_dicts': sorted_event_dicts[:self.MAX_EVENTS_SHOWN],
            'more_events_exist': len(sorted_event_dicts) > self.MAX_EVENTS_SHOWN,
            'articles': articles[:self.MAX_ARTICLES_SHOWN],
        })
        return context


class AdminPanelView(UserPassesTestMixin, TemplateView):
    template_name = 'web/admin_panel.html'
    possible_permissions = [
        'news.add_article', 'news.change_article', 'news.delete_article',
        'news.add_event', 'news.change_event', 'news.delete_event',
        'news.add_timeplace', 'news.change_timeplace', 'news.delete_timeplace',
        'make_queue.can_create_event_reservation',
        'make_queue.change_quota',
        'make_queue.change_printer3dcourse',
        'groups.can_edit_group',
        'makerspace.add_equipment', 'makerspace.change_equipment', 'makerspace.delete_equipment',
    ]

    def test_func(self):
        return any(self.request.user.has_perm(permission) for permission in self.possible_permissions)


class View404(TemplateView):
    template_name = 'web/404.html'

    def get(self, request, *args, **kwargs):
        return self.render_to_response({}, status=404)


def view_500(request):
    return render(request, template_name='web/500.html', status=500)


class AboutUsView(DisplayContentBoxView):
    template_name = 'web/about.html'
    title = 'about'
