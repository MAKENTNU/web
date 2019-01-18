import math

from datetime import timedelta
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import HttpResponseRedirect, JsonResponse, Http404
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import UpdateView, CreateView, TemplateView, DeleteView, DetailView

from news.forms import TimePlaceForm
from news.models import Article, Event, TimePlace
from web.templatetags.permission_tags import has_any_news_permissions


class ViewEventsView(TemplateView):
    template_name = 'news/events.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        past, future = [], []
        for event in Event.objects.filter(hidden=False):
            if not event.get_future_occurrences().exists() and not event.get_past_occurrences().exists():
                continue
            if event.multiday:
                if event.get_future_occurrences().exists():
                    future.append({
                        "first_occurrence": event.get_future_occurrences().first(),
                        "event": event,
                        "number_of_occurrences": event.timeplace_set.count(),
                    })
                else:
                    past.append({
                        "last_occurrence": event.get_past_occurrences().first(),
                        "event": event,
                        "number_of_occurrences": event.timeplace_set.count(),
                    })
            else:
                for occurrence in event.get_future_occurrences():
                    future.append({
                        "first_occurrence": occurrence,
                        "event": event,
                        "number_of_occurrences": 1,
                    })
                if event.get_past_occurrences().exists():
                    past.append({
                        "last_occurrence": event.get_past_occurrences().first(),
                        "event": event,
                        "number_of_occurrences": event.get_past_occurrences().count(),
                    })

        context.update({
            'past': sorted(past, key=lambda event: event["last_occurrence"].start_date, reverse=True),
            'future': sorted(future, key=lambda event: event["first_occurrence"].start_date),
        })
        return context


class ViewArticlesView(TemplateView):
    template_name = 'news/articles.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'articles': Article.objects.published().filter(),
        })
        return context


class ViewEventView(TemplateView):
    template_name = 'news/event.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event = get_object_or_404(Event, pk=kwargs['pk'])
        context.update({
            'article': event,
            'timeplaces': event.timeplace_set.all() if event.multiday else event.timeplace_set.future(),
        })
        if (event.hidden and not self.request.user.has_perm('news.change_event')) \
                or (event.private and not self.request.user.has_perm('news.can_view_private')):
            raise Http404()
        return context


class ViewArticleView(TemplateView):
    template_name = 'news/article.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        article = get_object_or_404(Article, pk=kwargs['pk'])
        context.update({
            'article': article,
        })
        if (article not in Article.objects.published() and not self.request.user.has_perm('news.change_article')) \
                or (article.private and not self.request.user.has_perm('news.can_view_private')):
            raise Http404()
        return context


class AdminView(TemplateView):
    template_name = 'news/admin.html'

    def get_context_data(self, **kwargs):
        if not has_any_news_permissions(self.request.user) and not self.request.user.is_superuser:
            raise Http404()
        context = super().get_context_data(**kwargs)
        context.update({
            'articles': Article.objects.all(),
            'events': Event.objects.all(),
        })
        return context


class AdminEventView(DetailView):
    template_name = 'news/admin_event.html'
    model = Event


class EditArticleView(PermissionRequiredMixin, UpdateView):
    model = Article
    template_name = 'news/article_edit.html'
    fields = (
        'title',
        'content',
        'clickbait',
        'image',
        'pub_date',
        'pub_time',
        'contain',
        'hidden',
        'private',
        'featured',
    )
    permission_required = (
        'news.change_article',
    )
    success_url = '/news/admin'


class CreateArticleView(PermissionRequiredMixin, CreateView):
    model = Article
    template_name = 'news/article_create.html'
    fields = (
        'title',
        'content',
        'clickbait',
        'image',
        'pub_date',
        'pub_time',
        'contain',
        'hidden',
        'private',
        'featured',
    )
    permission_required = (
        'news.add_article',
    )
    success_url = '/news/admin'


class EditEventView(PermissionRequiredMixin, UpdateView):
    model = Event
    template_name = 'news/event_edit.html'
    fields = (
        'title',
        'content',
        'clickbait',
        'image',
        'contain',
        'hidden',
        'private',
        'featured',
        'multiday',
    )
    permission_required = (
        'news.change_event',
    )

    def get_success_url(self):
        return reverse_lazy("admin-event", args=(self.object.id,))


class CreateEventView(PermissionRequiredMixin, CreateView):
    model = Event
    template_name = 'news/event_create.html'
    fields = (
        'title',
        'content',
        'clickbait',
        'image',
        'contain',
        'hidden',
        'private',
        'featured',
        'multiday',
    )
    permission_required = (
        'news.add_event',
    )

    def get_success_url(self):
        return reverse_lazy("admin-event", args=(self.object.id,))


class EditTimePlaceView(PermissionRequiredMixin, UpdateView):
    model = TimePlace
    template_name = 'news/timeplace_edit.html'
    form_class = TimePlaceForm
    permission_required = (
        'news.change_timeplace',
    )

    def get_form(self, form_class=None):
        form = self.form_class(**self.get_form_kwargs())
        if self.object.event.multiday:
            del form.fields["number_of_tickets"]
        return form

    def get_success_url(self):
        return reverse_lazy("admin-event", args=(self.object.event.id,))


class DuplicateTimePlaceView(PermissionRequiredMixin, View):
    permission_required = (
        'news.add_timeplace',
    )

    def get(self, request, pk):
        timeplace = get_object_or_404(TimePlace, pk=pk)
        now = timezone.now()
        if now.date() > timeplace.start_date:
            delta_days = (timezone.now().date() - timeplace.start_date).days
            weeks = math.ceil(delta_days / 7)
        else:
            weeks = 1
        timeplace.start_date += timedelta(weeks=weeks)
        if timeplace.end_date:
            timeplace.end_date += timedelta(weeks=weeks)
        timeplace.hidden = True
        timeplace.pk = None
        timeplace.save()
        return HttpResponseRedirect(reverse('timeplace-edit', args=(timeplace.pk,)))


class NewTimePlaceView(PermissionRequiredMixin, View):
    permission_required = (
        'news.add_timeplace',
    )

    def get(self, request, pk):
        event = get_object_or_404(Event, pk=pk)
        new_timeplace = TimePlace.objects.create(event=event)
        return HttpResponseRedirect(reverse('timeplace-edit', args=(new_timeplace.pk,)))


class AdminArticleToggleView(PermissionRequiredMixin, View):
    model = Article
    permission_required = (
        'news.change_article',
    )

    def post(self, request):
        pk, toggle = request.POST.get('pk'), request.POST.get('toggle')
        try:
            object = self.model.objects.get(pk=pk)
            val = not getattr(object, toggle)
            setattr(object, toggle, val)
            object.save()
            color = 'yellow' if val else 'grey'
        except (self.model.DoesNotExist, AttributeError):
            return JsonResponse({})

        return JsonResponse({
            'color': color,
        })


class AdminEventToggleView(AdminArticleToggleView):
    model = Event
    permission_required = (
        'news.change_event',
    )


class AdminTimeplaceToggleView(AdminArticleToggleView):
    model = TimePlace
    permission_required = (
        'news.change_timeplace',
    )


class DeleteArticleView(PermissionRequiredMixin, DeleteView):
    model = Article
    success_url = reverse_lazy('admin')
    permission_required = (
        'news.delete_article',
    )


class DeleteEventView(PermissionRequiredMixin, DeleteView):
    model = Event
    success_url = reverse_lazy('admin')
    permission_required = (
        'news.delete_event',
    )


class DeleteTimePlaceView(PermissionRequiredMixin, DeleteView):
    model = TimePlace
    success_url = reverse_lazy('admin')
    permission_required = (
        'news.delete_timeplace',
    )

    def get_success_url(self):
        return reverse_lazy("admin-event", args=(self.object.event.id,))
