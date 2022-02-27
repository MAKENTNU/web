import math
from abc import ABC, abstractmethod
from datetime import timedelta

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Count, Max, Prefetch, Q
from django.http import Http404, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.translation import get_language, gettext_lazy as _
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, RedirectView, TemplateView, UpdateView
from django.views.generic.edit import ModelFormMixin

from mail import email
from util.logging_utils import log_request_exception
from util.templatetags.permission_tags import has_any_article_permissions, has_any_event_permissions
from util.view_utils import CustomFieldsetFormMixin, PreventGetRequestsMixin
from .forms import ArticleForm, EventForm, EventRegistrationForm, NewsBaseForm, TimePlaceForm
from .models import Article, Event, EventTicket, NewsBase, TimePlace


class EventListView(TemplateView):
    template_name = 'news/event_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        future = Event.objects.future().visible_to(self.request.user).prefetch_related(
            'timeplaces',
            Prefetch('timeplaces',
                     queryset=TimePlace.objects.published().future().order_by('start_time'),
                     to_attr='future_timeplaces')
        )
        future_event_dicts = []
        for event in future:
            if not event.future_timeplaces:
                continue
            if event.standalone:
                future_event_dicts.append({
                    'event': event,
                    'shown_occurrence': event.future_timeplaces[0],
                    'number_of_occurrences': event.timeplaces.count(),
                })
            else:
                for timeplace in event.future_timeplaces:
                    future_event_dicts.append({
                        'event': event,
                        'shown_occurrence': timeplace,
                        'number_of_occurrences': 1,
                    })

        past = Event.objects.past().visible_to(self.request.user).annotate(
            latest_occurrence=Max('timeplaces__start_time'),
        ).order_by('-latest_occurrence').prefetch_related(
            Prefetch('timeplaces',
                     queryset=TimePlace.objects.published().past().order_by('-start_time'),
                     to_attr='past_timeplaces')
        )
        past_event_dicts = [{
            'event': event,
            'shown_occurrence': event.past_timeplaces[0],
            'number_of_occurrences': len(event.past_timeplaces),
        } for event in past if event.past_timeplaces]

        context.update({
            'future_event_dicts': sorted(future_event_dicts, key=lambda timeplace_: timeplace_['shown_occurrence'].start_time),
            'past_event_dicts': past_event_dicts,
        })
        return context


class ArticleListView(ListView):
    template_name = 'news/article_list.html'
    context_object_name = 'articles'

    def get_queryset(self):
        return Article.objects.published().visible_to(self.request.user).order_by('-publication_time')


class EventDetailView(TemplateView):
    template_name = 'news/event_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event = get_object_or_404(Event, pk=kwargs['pk'])
        future_timeplaces = event.timeplaces.published().future()
        context.update({
            'news_obj': event,
            'timeplaces': event.timeplaces.all() if event.standalone else future_timeplaces,
            'is_old': not future_timeplaces.exists(),
            'last_occurrence': event.get_past_occurrences().first(),
        })
        if (event.hidden and not self.request.user.has_perm('news.change_event')
                or event.private and not self.request.user.has_perm('news.can_view_private')):
            raise Http404()
        return context


class ArticleDetailView(TemplateView):
    template_name = 'news/article_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        article = get_object_or_404(Article, pk=kwargs['pk'])
        context.update({
            'news_obj': article,
        })
        if (article not in Article.objects.published() and not self.request.user.has_perm('news.change_article')
                or article.private and not self.request.user.has_perm('news.can_view_private')):
            raise Http404()
        return context


class AdminArticleListView(PermissionRequiredMixin, ListView):
    model = Article
    template_name = 'news/admin_article_list.html'
    context_object_name = 'articles'

    def has_permission(self):
        return has_any_article_permissions(self.request.user)


class AdminEventListView(PermissionRequiredMixin, ListView):
    model = Event
    template_name = 'news/admin_event_list.html'
    context_object_name = 'events'

    def has_permission(self):
        return has_any_event_permissions(self.request.user)

    def get_queryset(self):
        return Event.objects.annotate(
            latest_occurrence=Max('timeplaces__end_time'),
            num_future_occurrences=Count('timeplaces', filter=Q(timeplaces__end_time__gt=timezone.localtime())),
        ).order_by('-latest_occurrence').prefetch_related('timeplaces')


class AdminEventDetailView(DetailView):
    model = Event
    template_name = 'news/admin_event_detail.html'
    context_object_name = 'event'

    def get_context_data(self, **kwargs):
        event: Event = self.object
        return super().get_context_data(**{
            'future_timeplaces': event.timeplaces.future().order_by('start_time'),
            'past_timeplaces': event.timeplaces.past().order_by('-start_time'),
            **kwargs,
        })


class NewsBaseFormMixin(CustomFieldsetFormMixin, ABC):
    model: NewsBase
    form_class: NewsBaseForm
    template_name = 'news/news_base_edit.html'

    def get_custom_fieldsets(self):
        return [
            {'fields': ('title', 'content', 'clickbait')},
            self.get_custom_news_fieldset(),
            {'fields': ('image', 'contain')},
            {'fields': ('image_description',)},

            {'heading': _("Attributes")},
            {'fields': ('featured', 'hidden', 'private'), 'layout_class': "three inline"},
        ]

    @abstractmethod
    def get_custom_news_fieldset(self) -> dict:
        raise NotImplementedError


class ArticleFormMixin(NewsBaseFormMixin, ABC):
    model = Article
    form_class = ArticleForm
    success_url = reverse_lazy('admin_article_list')

    back_button_link = success_url
    back_button_text = _("Admin page for articles")

    def get_custom_news_fieldset(self) -> dict:
        return {'fields': ('publication_time',)}


class EditArticleView(PermissionRequiredMixin, ArticleFormMixin, UpdateView):
    permission_required = ('news.change_article',)

    form_title = _("Edit Article")


class CreateArticleView(PermissionRequiredMixin, ArticleFormMixin, CreateView):
    permission_required = ('news.add_article',)

    form_title = _("New Article")


class EventFormMixin(NewsBaseFormMixin, ModelFormMixin, ABC):
    model = Event
    form_class = EventForm
    template_name = 'news/event_edit.html'
    extra_context = {
        'Event': Event,  # for referencing Event.Type's choice values
    }

    def get_custom_news_fieldset(self) -> dict:
        return {'fields': ('event_type', 'number_of_tickets',), 'layout_class': "two"}

    def get_back_button_link(self):
        return self.get_success_url()

    def get_success_url(self):
        return reverse('admin_event_detail', args=(self.object.pk,))


class EditEventView(PermissionRequiredMixin, EventFormMixin, UpdateView):
    permission_required = ('news.change_event',)

    form_title = _("Edit Event")

    def get_back_button_text(self):
        return _("Admin page for “{event_title}”").format(event_title=self.object.title)


class CreateEventView(PermissionRequiredMixin, EventFormMixin, CreateView):
    permission_required = ('news.add_event',)

    form_title = _("New Event")
    back_button_text = _("Admin page for events")

    def get_back_button_link(self):
        return reverse('admin_event_list')


class TimePlaceFormMixin(CustomFieldsetFormMixin, ModelFormMixin, ABC):
    model = TimePlace
    form_class = TimePlaceForm
    template_name = 'news/timeplace_edit.html'

    @abstractmethod
    def get_event(self) -> Event:
        raise NotImplementedError

    def get_back_button_text(self):
        return _("Admin page for “{event_title}”").format(event_title=self.get_event().title)

    def get_custom_fieldsets(self):
        return [
            {'fields': ('event', 'place', 'place_url',
                        None if self.get_event().standalone else 'number_of_tickets',
                        'start_time', 'end_time', 'publication_time')},

            {'heading': _("Attributes")},
            {'fields': ('hidden',)},
        ]

    def get_success_url(self):
        return reverse('admin_event_detail', args=(self.object.event.pk,))


class EditTimePlaceView(PermissionRequiredMixin, TimePlaceFormMixin, UpdateView):
    permission_required = ('news.change_timeplace',)

    form_title = _("Edit Occurrence")

    def get_event(self) -> Event:
        return self.object.event

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if self.get_event().standalone:
            del form.fields["number_of_tickets"]
        return form

    def get_back_button_link(self):
        return self.get_success_url()


class CreateTimePlaceView(PermissionRequiredMixin, TimePlaceFormMixin, CreateView):
    permission_required = ('news.add_timeplace',)

    form_title = _("New Occurrence")

    def get_event(self) -> Event:
        return get_object_or_404(Event, pk=self.kwargs['event_pk'])

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        event = self.get_event()
        form.fields['event'].initial = event.pk
        if event.standalone:
            del form.fields['number_of_tickets']
        return form

    def get_back_button_link(self):
        return reverse('admin_event_detail', args=[self.get_event().pk])


class DuplicateTimePlaceView(PermissionRequiredMixin, View):
    permission_required = ('news.add_timeplace',)

    def get(self, request, pk):
        timeplace = get_object_or_404(TimePlace, pk=pk)
        if timezone.localtime() > timeplace.start_time:
            delta_days = (timezone.localtime() - timeplace.start_time).days
            weeks = math.ceil(delta_days / 7)
        else:
            weeks = 1
        timeplace.start_time += timedelta(weeks=weeks)
        timeplace.end_time += timedelta(weeks=weeks)
        timeplace.hidden = True
        timeplace.pk = None
        timeplace.save()
        return HttpResponseRedirect(reverse('timeplace_edit', args=(timeplace.pk,)))


class AdminArticleToggleView(PermissionRequiredMixin, View):
    permission_required = ('news.change_article',)
    model = Article

    def post(self, request):
        pk, toggle = request.POST.get('pk'), request.POST.get('toggle')
        try:
            obj = self.model.objects.get(pk=pk)
            val = not getattr(obj, toggle)
            setattr(obj, toggle, val)
            obj.save()
            color = 'yellow' if val else 'grey'
        except (self.model.DoesNotExist, AttributeError):
            return JsonResponse({})

        return JsonResponse({
            'color': color,
        })


class AdminEventToggleView(AdminArticleToggleView):
    permission_required = ('news.change_event',)
    model = Event


class AdminTimeplaceToggleView(AdminArticleToggleView):
    permission_required = ('news.change_timeplace',)
    model = TimePlace


class DeleteArticleView(PermissionRequiredMixin, PreventGetRequestsMixin, DeleteView):
    permission_required = ('news.delete_article',)
    model = Article
    success_url = reverse_lazy('admin_article_list')


class DeleteEventView(PermissionRequiredMixin, PreventGetRequestsMixin, DeleteView):
    permission_required = ('news.delete_event',)
    model = Event
    success_url = reverse_lazy('admin_event_list')


class DeleteTimePlaceView(PermissionRequiredMixin, PreventGetRequestsMixin, DeleteView):
    permission_required = ('news.delete_timeplace',)
    model = TimePlace

    def get_success_url(self):
        return reverse('admin_event_detail', args=(self.object.event.pk,))


class EventRegistrationView(CreateView):
    model = EventTicket
    form_class = EventRegistrationForm
    template_name = 'news/event_registration.html'

    @property
    def timeplace(self):
        if 'timeplace_pk' in self.kwargs:
            return get_object_or_404(TimePlace, pk=self.kwargs['timeplace_pk'])
        return None

    @property
    def event(self):
        if 'event_pk' in self.kwargs:
            return get_object_or_404(Event, pk=self.kwargs['event_pk'])
        return None

    def is_registration_allowed(self):
        return (self.timeplace and self.timeplace.can_register(self.request.user)
                or self.event and self.event.can_register(self.request.user))

    def dispatch(self, request, *args, **kwargs):
        if not self.is_registration_allowed():
            event = self.event or self.timeplace.event
            return HttpResponseRedirect(reverse('event_detail', kwargs={'pk': event.pk}))

        ticket = self.request.user.event_tickets.filter(active=True, timeplace=self.timeplace, event=self.event)
        if ticket.exists():
            return HttpResponseRedirect(reverse_lazy('ticket_detail', kwargs={'pk': ticket.first().pk}))
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        if not self.is_registration_allowed():
            form.add_error(None, _("Could not register you for the event, please try again later."))
            return self.form_invalid(form)

        form.instance.user = self.request.user
        form.instance.event = self.event
        form.instance.timeplace = self.timeplace
        ticket = form.save()

        try:
            async_to_sync(get_channel_layer().send)(
                'email', {
                    'type': 'send_html',
                    'html_render': email.render_html({'ticket': ticket}, 'email/ticket.html'),
                    'text': email.render_text({'ticket': ticket}, text_template_name='email/ticket.txt'),
                    'subject': str(_("Your ticket!")),  # pass the pure string object, instead of the proxy object from `gettext_lazy`
                    'from': settings.EVENT_TICKET_EMAIL,
                    'to': ticket.email,
                }
            )
        except Exception as e:
            log_request_exception("Sending event ticket email failed.", e, self.request)

        self.object = ticket
        return HttpResponseRedirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        event_title = (self.event or self.timeplace.event).title
        return super().get_context_data(**{
            'timeplace': self.timeplace,
            'event': self.event,
            'title': _("Register for the event “{title}”").format(title=event_title),
            **kwargs,
        })

    def get_success_url(self):
        return reverse('ticket_detail', args=[self.object.pk])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['initial'].update({
            'language': get_language(),
        })
        return kwargs


class TicketDetailView(LoginRequiredMixin, DetailView):
    model = EventTicket
    template_name = 'news/ticket_detail.html'
    context_object_name = 'ticket'


class MyTicketsListView(ListView):
    template_name = 'news/my_tickets_list.html'
    context_object_name = 'tickets'

    def get_queryset(self):
        return self.request.user.event_tickets.all()


class AdminEventTicketListView(TemplateView):
    template_name = 'news/admin_event_ticket_list.html'

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data()
        event = get_object_or_404(Event, pk=kwargs.pop('pk', 0))
        if not event.number_of_tickets:
            raise Http404()
        context_data.update({
            'tickets': event.tickets.order_by('-active'),
            'event': event,
            'object': event,
            'ticket_emails': ",".join(ticket.email for ticket in event.tickets.filter(active=True)),
        })
        return context_data


class AdminTimeplaceTicketListView(TemplateView):
    template_name = 'news/admin_event_ticket_list.html'

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data()
        timeplace = get_object_or_404(TimePlace, pk=kwargs.pop('pk', 0))
        if not timeplace.number_of_tickets:
            raise Http404()
        context_data.update({
            'tickets': timeplace.tickets.order_by('-active'),
            'event': timeplace.event,
            'object': timeplace,
            'ticket_emails': ",".join(ticket.email for ticket in timeplace.tickets.filter(active=True)),
        })
        return context_data


class CancelTicketView(LoginRequiredMixin, RedirectView):
    permanent = False
    query_string = True
    pattern_name = 'ticket_detail'

    def get_redirect_url(self, *args, **kwargs):
        ticket = get_object_or_404(EventTicket, pk=kwargs.get('pk', 0))

        # Allow for toggling if a ticket is canceled or not
        if self.request.user.has_perm('news.cancel_ticket'):
            ticket.active = not ticket.active
        elif self.request.user == ticket.user:
            ticket.active = False
        ticket.save()

        next_page = self.request.GET.get('next')
        if next_page is None:
            return super().get_redirect_url(*args, **kwargs)
        return next_page
