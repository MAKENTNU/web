import math
from abc import ABC, abstractmethod
from datetime import timedelta
from typing import Optional, Set

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
from util.logging_utils import log_request_exception
from util.view_utils import CleanNextParamMixin, CustomFieldsetFormMixin, PreventGetRequestsMixin, insert_form_field_values
from .forms import ArticleForm, EventForm, EventRegistrationForm, EventsSearchForm, NewsBaseForm, TimePlaceForm, ToggleForm
from .models import Article, Event, EventQuerySet, EventTicket, NewsBase, TimePlace


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
        return Article.objects.published().visible_to(self.request.user).order_by('-publication_time')


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
        return self.request.user.has_any_permissions_for(Article)


class AdminEventListView(PermissionRequiredMixin, ListView):
    model = Event
    template_name = 'news/admin_event_list.html'
    context_object_name = 'events'

    def has_permission(self):
        user = self.request.user
        return user.has_any_permissions_for(Event) or user.has_any_permissions_for(TimePlace)

    def get_queryset(self):
        return Event.objects.annotate(
            latest_occurrence=Max('timeplaces__end_time'),
            num_future_occurrences=Count('timeplaces', filter=Q(timeplaces__end_time__gt=timezone.localtime())),
        ).order_by('-latest_occurrence').prefetch_related('timeplaces')


class AdminEventsSearchView(PermissionRequiredMixin, FormView):
    form_class = EventsSearchForm
    template_name = 'news/admin_events_search.html'
    
    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        form = context_data['form']
        if form.is_bound:
            searched_name = form.cleaned_data['name']
            searched_name_split = searched_name.split()
            
            q=Q()
            for i in searched_name_split:
                q &= Q(first_name__icontains = i) | Q(last_name__icontains = i) | Q(username__icontains = i)

            users = User.objects.filter(q).prefetch_related(
                Prefetch('event_tickets',
                        queryset=EventTicket.objects.annotate(
                            first_standalone_event_occurrence=Min('event__timeplaces__start_time'),
                            last_standalone_event_occurrence=Max('event__timeplaces__start_time'),
                        ).select_related(
                            'timeplace',
                        ), to_attr='tickets'),
            )

            def sorting_key(tickets):
                if tickets.timeplace:
                    return tickets.timeplace.start_time
                else:
                    return tickets.first_standalone_event_occurrence

            for user in users:
                user.tickets = sorted(
                list(user.tickets),
                    key=sorting_key,
                )
            context_data.update({
                'users': users,
            })          

        return context_data

    def form_valid(self, form):
        return self.render_to_response(self.get_context_data(form=form))

    def has_permission(self):
        return has_any_event_permissions(self.request.user)


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


class EditArticleView(PermissionRequiredMixin, ArticleFormMixin, SpecificArticleView, UpdateView):
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
        return reverse('admin_event_detail', args=[self.object])


class EditEventView(PermissionRequiredMixin, EventFormMixin, SpecificEventView, UpdateView):
    permission_required = ('news.change_event',)

    form_title = _("Edit Event")

    def get_back_button_text(self):
        return _("Admin page for “{event_title}”").format(event_title=self.event.title)


class CreateEventView(PermissionRequiredMixin, EventFormMixin, CreateView):
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
        return insert_form_field_values(super().get_form_kwargs(), {'event': self.event})

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

    event: Event
    ticket_event: Optional[Event]
    ticket_time_place: Optional[TimePlace]

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.event = self.kwargs.get('event')
        time_place_pk = self.kwargs.get('time_place_pk')
        if time_place_pk is None:
            self.ticket_time_place = None
            self.ticket_event = self.event
        else:
            self.ticket_time_place = get_object_or_404(TimePlace, pk=time_place_pk, event=self.event)
            self.ticket_event = None

    def has_permission(self):
        return (
                self.ticket_time_place and self.ticket_time_place.can_register(self.request.user)
                or self.ticket_event and self.ticket_event.can_register(self.request.user, fail_if_not_standalone=True)
        )

    def dispatch(self, request, *args, **kwargs):
        # If the user already has an active ticket for the event/timeplace, redirect to that ticket
        try:
            ticket = self.request.user.event_tickets.get(active=True, timeplace=self.ticket_time_place, event=self.ticket_event)
        except EventTicket.DoesNotExist:
            pass
        else:
            return HttpResponseRedirect(reverse('ticket_detail', args=[ticket.pk]))
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        try:
            existing_ticket_for_user = EventTicket.objects.get(user=self.request.user, timeplace=self.ticket_time_place, event=self.ticket_event)
        except EventTicket.DoesNotExist:
            # If this is a completely new ticket, set the initial language to the user-set site language
            kwargs['initial']['language'] = get_language()
        else:
            # If a user already has an existing ticket for the timeplace/event, use this as the instance
            kwargs['instance'] = existing_ticket_for_user

        # Forcefully insert the user, time place and event into the form
        return insert_form_field_values(kwargs, {
            'user': self.request.user,
            'timeplace': self.ticket_time_place,
            'event': self.ticket_event,
        })

    def form_valid(self, form):
        form.instance.active = True  # this is done mainly for reactivating an existing ticket
        ticket = form.save()
        self.object = ticket

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

        return HttpResponseRedirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        return super().get_context_data(**{
            'title': _("Register for the event “{title}”").format(title=self.event.title),
            **kwargs,
        })

    def get_success_url(self):
        return reverse('ticket_detail', args=[self.object.pk])


class TicketDetailView(DetailView):
    model = EventTicket
    template_name = 'news/ticket_detail.html'
    context_object_name = 'ticket'


class MyTicketsListView(ListView):
    template_name = 'news/my_tickets_list.html'
    context_object_name = 'tickets'

    def get_queryset(self):
        return self.request.user.event_tickets.prefetch_related(
            'event__timeplaces__event', 'timeplace__event',
        )


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


class CancelTicketView(PermissionRequiredMixin, CleanNextParamMixin, UpdateView):
    model = EventTicket
    fields = ()
    template_name = 'news/ticket_cancel.html'
    context_object_name = 'ticket'

    ticket: EventTicket

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.ticket = self.get_object()

    def has_permission(self):
        return (
                self.request.user.has_perm('news.cancel_ticket')
                or self.request.user == self.ticket.user
        )

    def get_allowed_next_params(self) -> Set[str]:
        return {
            reverse('ticket_detail', args=[self.ticket.pk]),
            reverse('my_tickets_list'),
            reverse('event_detail', args=[self.ticket.registered_event]),
        }

    def get_queryset(self):
        return self.request.user.event_tickets.all()

    def get_context_data(self, **kwargs):
        if self.ticket.timeplace:
            at_time_string = _(" at {time}").format(time=short_datetime_format(self.ticket.timeplace.start_time))
        else:
            at_time_string = ""
        heading = _("Are you sure you want to cancel your ticket for<br/>“{event}”{at_time_string}?").format(
            event=self.ticket.registered_event, at_time_string=at_time_string,
        )
        return super().get_context_data(**{
            'event': self.ticket.registered_event,
            'heading': heading,
            **kwargs,
        })

    def get(self, request, *args, **kwargs):
        if not self.ticket.active:
            # Redirect back to the ticket, as it would be confusing to show a page
            # asking if you want to cancel the ticket if it's already canceled
            return HttpResponseRedirect(self.get_success_url())
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        # Allow for toggling if a ticket is canceled or not
        if self.request.user.has_perm('news.cancel_ticket'):
            self.ticket.active = not self.ticket.active
            self.ticket.save()
        elif self.request.user == self.ticket.user and self.ticket.active:
            self.ticket.active = False
            self.ticket.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        if self.cleaned_next_param:
            return self.cleaned_next_param
        return reverse('ticket_detail', args=[self.ticket.pk])
