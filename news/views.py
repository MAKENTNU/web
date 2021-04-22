import logging
import math
from abc import ABC, abstractmethod
from datetime import timedelta

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import Count, Max, Prefetch, Q
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.translation import get_language, gettext_lazy as _
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, FormView, ListView, UpdateView
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.edit import ModelFormMixin

from mail import email
from util.locale_utils import short_datetime_format
from util.templatetags.permission_tags import has_any_article_permissions, has_any_event_permissions
from util.view_utils import CustomFieldsetFormMixin, PreventGetRequestsMixin, insert_form_field_values
from .forms import ArticleForm, EventForm, EventRegistrationForm, TimePlaceForm, ToggleForm
from .models import Article, Event, EventQuerySet, EventTicket, TimePlace


class SpecificArticleView(SingleObjectMixin, View, ABC):
    article: Article

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.article = kwargs['article']

    def get_object(self, queryset=None):
        return self.article


class EventBasedView(View, ABC):
    event: Event

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.event = kwargs['event']


class SpecificEventView(SingleObjectMixin, EventBasedView, ABC):

    def get_object(self, queryset=None):
        return self.event


class SpecificTimePlaceView(SingleObjectMixin, EventBasedView, ABC):
    time_place: TimePlace

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.time_place = self.get_object()

    def get_queryset(self):
        return self.event.timeplaces.all()


class EventListView(ListView):
    template_name = 'news/event_list.html'

    def get_queryset(self):
        return Event.objects.visible_to(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset: EventQuerySet = self.get_queryset()

        future = queryset.future().prefetch_related(
            'timeplaces',
            Prefetch('timeplaces',
                     queryset=TimePlace.objects.published().future().order_by('start_time'),
                     to_attr='future_timeplaces')
        )
        future_event_dicts = []
        for event in future:
            if not event.future_timeplaces:
                continue
            if event.event_type == Event.Type.STANDALONE:
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

        past = queryset.past().annotate(
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
        return Article.objects.published().visible_to(self.request.user)


class EventDetailView(PermissionRequiredMixin, SpecificEventView, DetailView):
    model = Event
    template_name = 'news/event_detail.html'
    context_object_name = 'news_obj'

    def has_permission(self):
        if self.event.hidden and not self.request.user.has_perm('news.change_event'):
            return False
        elif self.event.private and not self.request.user.has_perm('news.can_view_private'):
            return False
        else:
            return True

    def get_context_data(self, **kwargs):
        future_timeplaces = self.event.timeplaces.published().future()
        return super().get_context_data(**{
            'timeplaces': self.event.timeplaces.all() if self.event.standalone else future_timeplaces,
            'is_old': not future_timeplaces.exists(),
            'last_occurrence': self.event.get_past_occurrences().first(),
            **kwargs,
        })


class ArticleDetailView(PermissionRequiredMixin, SpecificArticleView, DetailView):
    model = Article
    template_name = 'news/article_detail.html'
    context_object_name = 'news_obj'

    def has_permission(self):
        if self.article not in Article.objects.published() and not self.request.user.has_perm('news.change_article'):
            return False
        elif self.article.private and not self.request.user.has_perm('news.can_view_private'):
            return False
        else:
            return True


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


class AdminEventDetailView(PermissionRequiredMixin, SpecificEventView, DetailView):
    permission_required = ('news.change_event',)
    model = Event
    template_name = 'news/admin_event_detail.html'
    context_object_name = 'event'

    def get_context_data(self, **kwargs):
        return super().get_context_data(**{
            'future_timeplaces': self.event.timeplaces.future().order_by('start_time'),
            'past_timeplaces': self.event.timeplaces.past().order_by('-start_time'),
            **kwargs,
        })


class NewsBaseEditMixin(CustomFieldsetFormMixin, ABC):
    template_name = 'news/news_base_edit.html'

    def get_custom_fieldsets(self):
        return [
            {'fields': ('title', 'content', 'clickbait')},
            self.get_custom_news_fieldset(),
            {'fields': ('image', 'contain')},

            {'heading': _("Attributes")},
            {'fields': ('featured', 'hidden', 'private'), 'layout_class': "three inline"},
        ]

    @abstractmethod
    def get_custom_news_fieldset(self) -> dict:
        raise NotImplementedError


class ArticleEditMixin(NewsBaseEditMixin, ABC):
    model = Article
    form_class = ArticleForm
    success_url = reverse_lazy('admin_article_list')

    back_button_link = success_url
    back_button_text = _("Admin page for articles")

    def get_custom_news_fieldset(self) -> dict:
        return {'fields': ('publication_time',)}


class EditArticleView(PermissionRequiredMixin, ArticleEditMixin, SpecificArticleView, UpdateView):
    permission_required = ('news.change_article',)

    form_title = _("Edit Article")


class CreateArticleView(PermissionRequiredMixin, ArticleEditMixin, CreateView):
    permission_required = ('news.add_article',)

    form_title = _("New Article")


class EventEditMixin(NewsBaseEditMixin, ModelFormMixin, ABC):
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
        return reverse('admin_event_detail', args=[self.object])


class EditEventView(PermissionRequiredMixin, EventEditMixin, SpecificEventView, UpdateView):
    permission_required = ('news.change_event',)

    form_title = _("Edit Event")

    def get_back_button_text(self):
        return _("Admin page for “{event_title}”").format(event_title=self.event.title)


class CreateEventView(PermissionRequiredMixin, EventEditMixin, CreateView):
    permission_required = ('news.add_event',)

    form_title = _("New Event")
    back_button_text = _("Admin page for events")

    def get_back_button_link(self):
        return reverse('admin_event_list')


class BaseTimePlaceEditView(CustomFieldsetFormMixin, EventBasedView, ABC):
    model = TimePlace
    form_class = TimePlaceForm
    template_name = 'news/timeplace_edit.html'

    def get_form_kwargs(self):
        # Forcefully pass the event from the URL to the form
        return insert_form_field_values(super().get_form_kwargs(), ('event', self.event))

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if self.event.standalone:
            del form.fields['number_of_tickets']
        return form

    def get_back_button_link(self):
        return self.get_success_url()

    def get_back_button_text(self):
        return _("Admin page for “{event_title}”").format(event_title=self.event.title)

    def get_custom_fieldsets(self):
        return [
            {'fields': ('event', 'place', 'place_url',
                        None if self.event.standalone else 'number_of_tickets',
                        'start_time', 'end_time', 'publication_time')},

            {'heading': _("Attributes")},
            {'fields': ('hidden',)},
        ]

    def get_success_url(self):
        return reverse('admin_event_detail', args=[self.event])


class EditTimePlaceView(PermissionRequiredMixin, SpecificTimePlaceView, BaseTimePlaceEditView, UpdateView):
    permission_required = ('news.change_timeplace',)

    form_title = _("Edit Occurrence")


class CreateTimePlaceView(PermissionRequiredMixin, BaseTimePlaceEditView, CreateView):
    permission_required = ('news.add_timeplace',)

    form_title = _("New Occurrence")


class DuplicateTimePlaceView(PermissionRequiredMixin, PreventGetRequestsMixin, SpecificTimePlaceView, CreateView):
    permission_required = ('news.add_timeplace',)
    fields = ()

    def form_valid(self, form):
        if timezone.localtime() > self.time_place.start_time:
            delta_days = (timezone.localtime() - self.time_place.start_time).days
            weeks = math.ceil(delta_days / 7)
        else:
            weeks = 1
        self.time_place.pk = None  # duplicates the object when saving
        self.time_place.start_time += timedelta(weeks=weeks)
        self.time_place.end_time += timedelta(weeks=weeks)
        self.time_place.hidden = True
        self.time_place.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('timeplace_edit', args=[self.event, self.time_place.pk])


class AdminNewsBaseToggleView(PreventGetRequestsMixin, SingleObjectMixin, FormView, ABC):
    form_class = ToggleForm

    def get_form_kwargs(self):
        return {
            **super().get_form_kwargs(),
            'instance': self.get_object(),
        }

    def form_valid(self, form):
        obj = self.get_object()
        toggle_attr = form.cleaned_data['toggle_attr']
        attr_value = getattr(obj, toggle_attr)

        toggled_attr_value = not attr_value
        setattr(obj, toggle_attr, toggled_attr_value)
        obj.save()
        return JsonResponse({
            'color': 'yellow' if toggled_attr_value else 'grey',
        })

    def form_invalid(self, form):
        return JsonResponse({})


class AdminArticleToggleView(PermissionRequiredMixin, SpecificArticleView, AdminNewsBaseToggleView):
    permission_required = ('news.change_article',)


class AdminEventToggleView(PermissionRequiredMixin, SpecificEventView, AdminNewsBaseToggleView):
    permission_required = ('news.change_event',)


class AdminTimeplaceToggleView(PermissionRequiredMixin, SpecificTimePlaceView, AdminNewsBaseToggleView):
    permission_required = ('news.change_timeplace',)


class DeleteArticleView(PermissionRequiredMixin, PreventGetRequestsMixin, SpecificArticleView, DeleteView):
    permission_required = ('news.delete_article',)
    model = Article
    success_url = reverse_lazy('admin_article_list')


class DeleteEventView(PermissionRequiredMixin, PreventGetRequestsMixin, SpecificEventView, DeleteView):
    permission_required = ('news.delete_event',)
    model = Event
    success_url = reverse_lazy('admin_event_list')


class DeleteTimePlaceView(PermissionRequiredMixin, PreventGetRequestsMixin, SpecificTimePlaceView, DeleteView):
    permission_required = ('news.delete_timeplace',)
    model = TimePlace

    def get_success_url(self):
        return reverse('admin_event_detail', args=[self.object.event])


class EventRegistrationView(PermissionRequiredMixin, CreateView):
    model = EventTicket
    form_class = EventRegistrationForm
    template_name = 'news/event_registration.html'

    event: Event = None
    time_place: TimePlace = None

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.event = self.kwargs.get('event')
        time_place_pk = self.kwargs.get('time_place_pk')
        if time_place_pk is not None:
            self.time_place = get_object_or_404(TimePlace, pk=time_place_pk)

    def has_permission(self):
        return (
                self.time_place and self.time_place.can_register(self.request.user)
                or self.event and self.event.can_register(self.request.user)
        )

    def dispatch(self, request, *args, **kwargs):
        # If the user already has an active ticket for the event/timeplace, redirect to that ticket
        ticket = self.request.user.event_tickets.filter(active=True, timeplace=self.time_place, event=self.event)
        if ticket.exists():
            return HttpResponseRedirect(reverse('ticket_detail', args=[ticket.first().pk]))
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.event = self.event
        form.instance.timeplace = self.time_place
        ticket = form.save()

        try:
            async_to_sync(get_channel_layer().send)(
                'email', {
                    'type': 'send_html',
                    'html_render': email.render_html({'ticket': ticket}, 'email/ticket.html'),
                    'text': email.render_text({'ticket': ticket}, text_template_name='email/ticket.txt'),
                    'subject': _("Your ticket!"),
                    'from': settings.EVENT_TICKET_EMAIL,
                    'to': ticket.email,
                }
            )
        except Exception as e:
            logging.getLogger('django.request').exception("Sending event ticket email failed.", exc_info=e)

        self.object = ticket
        return HttpResponseRedirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        event_title = (self.event or self.time_place.event).title
        return super().get_context_data(**{
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


class TicketDetailView(DetailView):
    model = EventTicket
    template_name = 'news/ticket_detail.html'
    context_object_name = 'ticket'


class MyTicketsListView(ListView):
    template_name = 'news/my_tickets_list.html'
    context_object_name = 'tickets'

    def get_queryset(self):
        return self.request.user.event_tickets.all()


class AdminEventTicketListView(PermissionRequiredMixin, EventBasedView, ListView):
    model = EventTicket
    template_name = 'news/admin_event_ticket_list.html'
    context_object_name = 'tickets'

    @property
    def focused_object(self):
        return self.event

    def has_permission(self):
        return self.request.user.has_perm('news.change_event') and self.focused_object.number_of_tickets

    def get_queryset(self):
        return self.focused_object.tickets.order_by('-active')

    def get_context_data(self, **kwargs):
        return super().get_context_data(**{
            'event': self.event,
            'focused_object': self.focused_object,
            'ticket_emails': ",".join(ticket.email for ticket in self.focused_object.tickets.filter(active=True)),
            **kwargs,
        })


class AdminTimeplaceTicketListView(AdminEventTicketListView):
    time_place_pk_url_kwarg = 'pk'
    time_place: TimePlace

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.time_place = get_object_or_404(self.event.timeplaces, pk=self.kwargs[self.time_place_pk_url_kwarg])

    @property
    def focused_object(self):
        return self.time_place


class CancelTicketView(PermissionRequiredMixin, UpdateView):
    model = EventTicket
    fields = ()
    template_name = 'news/ticket_cancel.html'
    context_object_name = 'ticket'

    object: EventTicket

    def has_permission(self):
        return (
                self.request.user.has_perm('news.cancel_ticket')
                or self.request.user == self.object.user
        )

    def get_queryset(self):
        return self.request.user.event_tickets.all()

    def get_context_data(self, **kwargs):
        ticket = self.object
        event = ticket.event or ticket.timeplace.event
        if ticket.timeplace:
            at_time_string = _(" at {time}").format(time=short_datetime_format(ticket.timeplace.start_time))
        else:
            at_time_string = ""
        heading = _("Are you sure you want to cancel your ticket for<br/>“{event}”{at_time_string}?").format(
            event=event, at_time_string=at_time_string,
        )
        return super().get_context_data(**{
            'event': event,
            'heading': heading,
            **kwargs,
        })

    def get(self, request, *args, **kwargs):
        ticket = self.get_object()
        if not ticket.active:
            # Redirect back to the ticket, as it would be confusing to show a page
            # asking if you want to cancel the ticket if it's already canceled
            return HttpResponseRedirect(self.get_success_url())
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        ticket = self.object
        # Allow for toggling if a ticket is canceled or not
        if self.request.user.has_perm('news.cancel_ticket'):
            ticket.active = not ticket.active
            ticket.save()
        elif self.request.user == ticket.user and ticket.active:
            ticket.active = False
            ticket.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        next_page = self.request.GET.get('next')
        if next_page is not None:
            return next_page
        return reverse('ticket_detail', args=[self.object.pk])
