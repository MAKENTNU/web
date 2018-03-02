from datetime import timedelta

import math
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import UpdateView, CreateView, TemplateView

from news.models import Article, Event, TimePlace


class ViewEventsView(TemplateView):
    template_name = 'news/events.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'past': TimePlace.objects.past(),
            'future': TimePlace.objects.future(),
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
        context.update({
            'article': get_object_or_404(Event, pk=kwargs['pk']),
        })
        return context


class ViewArticleView(TemplateView):
    template_name = 'news/article.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'article': get_object_or_404(Article, pk=kwargs['pk']),
        })
        return context


class AdminView(TemplateView):
    template_name = 'news/admin.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'articles': Article.objects.all(),
            'events': Event.objects.all(),
        })
        return context


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
    success_url = '/'


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
    success_url = '/'


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
    )
    permission_required = (
        'news.change_event',
    )
    success_url = '/'


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
    )
    permission_required = (
        'news.add_event',
    )
    success_url = '/'


class EditTimePlaceView(PermissionRequiredMixin, UpdateView):
    model = TimePlace
    template_name = 'news/timeplace_edit.html'
    fields = (
        'event',
        'pub_date',
        'pub_time',
        'start_date',
        'end_date',
        'start_time',
        'end_time',
        'place',
        'place_url',
        'hoopla',
        'hidden',
    )
    permission_required = (
        'news.change_timeplace',
    )
    success_url = '/'

    def post(self, request, *args, **kwargs):
        pk = get_object_or_404(TimePlace, pk=kwargs['pk']).event.pk
        self.success_url = reverse('event', args=(pk,))
        return super().post(request, *args, **kwargs)


class CreateTimePlaceView(PermissionRequiredMixin, CreateView):
    model = TimePlace
    template_name = 'news/timeplace_create.html'
    fields = (
        'event',
        'pub_date',
        'pub_time',
        'start_date',
        'end_date',
        'start_time',
        'end_time',
        'place',
        'place_url',
        'hoopla',
        'hidden',
    )
    permission_required = (
        'news.add_timeplace',
    )
    success_url = '/'


class DuplicateTimePlaceView(PermissionRequiredMixin, View):
    permission_required = (
        'news.add_timeplace',
    )

    def get(self, request, pk):
        timeplace = get_object_or_404(TimePlace, pk=pk)
        now = timezone.now()
        if now.date() > timeplace.start_date or now.date() == timeplace.start_date and now.time() > timeplace.start_time:
            delta_days = timezone.now().date() - timeplace.start_date
            weeks = math.ceil(delta_days / 7)
        else:
            weeks = 1
        timeplace.start_date += timedelta(weeks=weeks)
        timeplace.pub_date += timedelta(weeks=weeks)
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
