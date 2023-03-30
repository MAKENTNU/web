from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import Prefetch
from django.views.generic import TemplateView

from announcements.models import Announcement
from contentbox.views import DisplayContentBoxView
from faq.models import Category, Question
from groups.models import Committee
from make_queue.models.course import Printer3DCourse
from make_queue.models.reservation import Quota
from makerspace.models import Equipment
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


class AdminPanelView(PermissionRequiredMixin, TemplateView):
    MODEL_LIST = [
        Article, Event, TimePlace,
        Printer3DCourse, Quota,
        Equipment,
        Category, Question,
        Committee,
        Announcement,
    ]
    # Extra permissions that are not among the `add`, `change` or `delete` permissions of the models in `MODEL_LIST`
    EXTRA_PERMS = [
        'make_queue.can_create_event_reservation',
    ]

    template_name = 'web/admin_panel.html'

    def has_permission(self):
        from util.templatetags.permission_tags import can_view_admin_panel  # Avoids circular importing

        return can_view_admin_panel(self.request.user)


class AboutUsView(DisplayContentBoxView):
    template_name = 'web/about.html'
