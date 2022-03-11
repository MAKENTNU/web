from django.contrib.auth.mixins import UserPassesTestMixin
from django.db.models import Prefetch
from django.shortcuts import render
from django.views.generic import TemplateView

from contentbox.views import DisplayContentBoxView
from news.models import Article, Event, TimePlace


class IndexView(TemplateView):
    MAX_EVENTS_SHOWN = 4
    MAX_ARTICLES_SHOWN = 4

    template_name = 'web/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        future_events = Event.objects.future().visible_to(self.request.user).prefetch_related(
            'timeplaces',
            Prefetch('timeplaces',
                     queryset=TimePlace.objects.published().future().order_by('start_time'),
                     to_attr='future_timeplaces')
        )
        future_event_dicts = [{
            'event': event,
            'shown_occurrence': event.future_timeplaces[0],
            'number_of_occurrences': event.timeplaces.count() if event.standalone else len(event.future_timeplaces),
        } for event in future_events if event.future_timeplaces]

        sorted_future_event_dicts = sorted(future_event_dicts, key=lambda event: event['shown_occurrence'].start_time)
        articles = Article.objects.published().visible_to(self.request.user).filter(featured=True).order_by('-publication_time')
        context.update({
            'featured_event_dicts': sorted_future_event_dicts[:self.MAX_EVENTS_SHOWN],
            'more_events_exist': len(sorted_future_event_dicts) > self.MAX_EVENTS_SHOWN,
            'featured_articles': articles[:self.MAX_ARTICLES_SHOWN],
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
