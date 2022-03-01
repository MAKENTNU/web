from django.contrib import admin
from django.db.models import Count, Max, Prefetch, Q, QuerySet
from django.template.loader import get_template
from django.utils import timezone
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.text import capfirst
from django.utils.translation import gettext_lazy as _
from simple_history.admin import SimpleHistoryAdmin

from util import html_utils
from util.admin_utils import TextFieldOverrideMixin, link_to_admin_change_form, list_filter_factory, search_escaped_and_unescaped
from util.locale_utils import short_datetime_format
from web.multilingual.admin import MultiLingualFieldAdmin
from .forms import ArticleForm, EventForm, NewsBaseForm
from .models import Article, Event, EventTicket, NewsBase, TimePlace


class NewsBaseAdmin(MultiLingualFieldAdmin, SimpleHistoryAdmin):
    form_base: NewsBaseForm
    list_display_extra: tuple

    list_filter = ('featured', 'hidden', 'private')
    search_fields = ('title', 'content', 'clickbait')
    list_editable = ('contain', 'featured', 'hidden', 'private')
    list_display = ('__str__', *list_editable)  # prevents Django system check errors; the field is actually set in `get_list_display()` below

    readonly_fields = ('last_modified',)

    def get_list_display(self, request):
        return (
            'title',
            *self.list_display_extra,
            'get_image', 'contain', 'featured', 'hidden', 'private', 'last_modified',
        )

    @admin.display(description=_("image"))
    def get_image(self, news_obj: NewsBase):
        return html_utils.tag_media_img(news_obj.image.url, url_host_name='main', alt_text=news_obj.image_description)

    def get_form(self, request, obj: NewsBase = None, **kwargs):
        return super().get_form(request, **{
            'help_texts': self.form_base.Meta.help_texts,
            **kwargs,
        })

    def get_search_results(self, request, queryset, search_term):
        return search_escaped_and_unescaped(super(), request, queryset, search_term)


class ArticleAdmin(NewsBaseAdmin):
    form_base = ArticleForm
    list_display_extra = ('publication_time',)

    ordering = ('-publication_time',)


def get_ticket_table(tickets: QuerySet[EventTicket]):
    ticket_dicts = [
        {
            'ref_link': link_to_admin_change_form(ticket, text=ticket.pk),
            'user_name_link': link_to_admin_change_form(ticket.user, text=ticket.name) if ticket.user else "-",
            'user_email': ticket.email,
            'comment': ticket.comment,
            'language': ticket.get_language_display(),
        }
        for ticket in tickets.select_related('user')
    ]
    return get_template('admin/news/event/change_form_ticket_table.html').render({
        'ticket_dicts': ticket_dicts,
    })


class TimePlaceInline(TextFieldOverrideMixin, admin.TabularInline):
    model = TimePlace
    ordering = ('-start_time',)

    readonly_fields = ('get_num_reserved_tickets', 'last_modified')
    show_change_link = True

    extra = 0

    @admin.display(description=_("number of reserved tickets"))
    def get_num_reserved_tickets(self, time_place: TimePlace):
        return time_place.ticket_count

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.select_related('event')
        return qs.annotate(ticket_count=Count('tickets', filter=Q(tickets__active=True)))  # facilitates querying `ticket_count`


class EventAdmin(NewsBaseAdmin):
    MAX_TICKET_OCCURRENCES_LISTED = 20
    form_base = EventForm
    list_display_extra = ('event_type', 'get_num_occurrences', 'get_future_occurrences', 'get_last_occurrence', 'get_number_of_tickets')

    list_filter = ('event_type', *NewsBaseAdmin.list_filter)

    inlines = [TimePlaceInline]
    fieldsets = (
        (None, {
            'fields': (
                'title', 'content', 'clickbait', 'image', 'image_description', 'contain', 'featured', 'hidden', 'private',
                'event_type', 'number_of_tickets', 'last_modified',
            ),
        }),
        # `capfirst()` to avoid duplicate translation differing only in case
        (capfirst(_("tickets")), {
            'fields': ('get_active_tickets', 'get_inactive_tickets'),
            'classes': ('collapse',),
        }),
    )
    readonly_fields = (*NewsBaseAdmin.readonly_fields, 'get_active_tickets', 'get_inactive_tickets')

    @admin.display(
        ordering='num_time_places',
        description=_("number of occurrences"),
    )
    def get_num_occurrences(self, event: Event):
        return event.num_time_places

    @admin.display(description=_("future occurrences"))
    def get_future_occurrences(self, event: Event):
        occurrence_strings = [
            link_to_admin_change_form(time_place, text=short_datetime_format(time_place.start_time))
            for time_place in event.future_time_places
        ]
        return html_utils.block_join(occurrence_strings, sep="<b>&bull;</b>") or None

    @admin.display(description=_("previous occurrence"))
    def get_last_occurrence(self, event: Event):
        if not event.past_time_places:
            return None
        last_occurrence = event.past_time_places[0]
        occurrence_string = link_to_admin_change_form(last_occurrence, text=short_datetime_format(last_occurrence.start_time))
        # Use `block_join()` to format the rendered occurrence string in the same way as the other columns
        return html_utils.block_join([occurrence_string], sep="")

    @admin.display(description=_("number of reserved tickets"))
    def get_number_of_tickets(self, event: Event):
        if event.standalone:
            return f"{event.ticket_count}/{event.number_of_tickets}"
        else:
            time_place_ticket_strings = [
                mark_safe(
                    f"{time_place.ticket_count}/{time_place.number_of_tickets}&emsp;"
                    + link_to_admin_change_form(time_place, text=f"({short_datetime_format(time_place.start_time)})")
                )
                for time_place in event.existing_time_places
            ]
            if len(time_place_ticket_strings) > self.MAX_TICKET_OCCURRENCES_LISTED:
                truncated_strings_count = len(time_place_ticket_strings[self.MAX_TICKET_OCCURRENCES_LISTED:])
                time_place_ticket_strings = time_place_ticket_strings[:self.MAX_TICKET_OCCURRENCES_LISTED]
                time_place_ticket_strings.append(_("{count} more...").format(count=truncated_strings_count))

            return html_utils.block_join(time_place_ticket_strings, sep="<b>&bull;</b>") or None

    @admin.display(description=_("active tickets"))
    def get_active_tickets(self, event: Event):
        return get_ticket_table(event.tickets.filter(active=True))

    @admin.display(description=_("inactive tickets"))
    def get_inactive_tickets(self, event: Event):
        return get_ticket_table(event.tickets.filter(active=False))

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Passing `distinct=True` to make multiple aggregations work
        # (see https://docs.djangoproject.com/en/stable/topics/db/aggregation/#combining-multiple-aggregations)
        qs = qs.annotate(
            num_time_places=Count('timeplaces', distinct=True),  # facilitates querying `num_time_places`;
            ticket_count=Count('tickets', filter=Q(tickets__active=True), distinct=True),  # facilitates querying `ticket_count`
        )
        qs = qs.prefetch_related(
            Prefetch('timeplaces',
                     queryset=TimePlace.objects.annotate(
                         ticket_count=Count('tickets', filter=Q(tickets__active=True)),
                     ).order_by('-start_time'),
                     to_attr='existing_time_places'),  # facilitates querying `ticket_count` for each `existing_time_places`
            Prefetch('timeplaces',
                     queryset=TimePlace.objects.future().order_by('-start_time'),
                     to_attr='future_time_places'),
            Prefetch('timeplaces',
                     queryset=TimePlace.objects.past().order_by('-start_time'),
                     to_attr='past_time_places'),
        )
        return qs.annotate(latest_occurrence=Max('timeplaces__start_time')).order_by('-latest_occurrence')


class TimePlaceAdmin(TextFieldOverrideMixin, admin.ModelAdmin):
    list_display = (
        'publication_time', 'get_event', 'start_time', 'end_time', 'get_place', 'number_of_tickets', 'get_num_reserved_tickets',
        'hidden', 'is_published', 'last_modified',
    )
    list_filter = (
        'event__event_type',
        list_filter_factory(
            _("is published"), 'is_published', lambda qs, yes_filter: qs.published() if yes_filter else qs.unpublished(),
        ),
    )
    search_fields = (
        'place', 'place_url',
        *(f'event__{field}' for field in EventAdmin.search_fields),
    )
    list_editable = ('number_of_tickets', 'hidden')
    ordering = ('-start_time',)
    list_select_related = ('event',)

    fieldsets = (
        (None, {
            'fields': (
                'event', 'publication_time', 'start_time', 'end_time', 'place', 'place_url', 'hidden', 'number_of_tickets', 'last_modified',
            ),
        }),
        # `capfirst()` to avoid duplicate translation differing only in case
        (capfirst(_("tickets")), {
            'fields': ('get_active_tickets', 'get_inactive_tickets'),
            'classes': ('collapse',),
        }),
    )
    readonly_fields = ('last_modified', 'get_active_tickets', 'get_inactive_tickets')
    raw_id_fields = ('event',)

    @admin.display(
        ordering='event__title',
        description=_("event"),
    )
    def get_event(self, time_place: TimePlace):
        return link_to_admin_change_form(time_place.event)

    @admin.display(
        ordering='place',
        description=_("location"),
    )
    def get_place(self, time_place: TimePlace):
        return format_html('<a href="{}" target="_blank">{}</a>', time_place.place_url, time_place.place)

    @admin.display(
        ordering='ticket_count',
        description=_("number of reserved tickets"),
    )
    def get_num_reserved_tickets(self, time_place: TimePlace):
        if time_place.event.standalone:
            standalone_notice = _("event is standalone")
            return mark_safe(f"- <i>({standalone_notice})</i>")
        else:
            return time_place.ticket_count

    @admin.display(description=_("is published"))
    def is_published(self, time_place: TimePlace):
        if time_place.event.hidden:
            unpublished_message = _("event hidden")
        elif time_place.hidden:
            unpublished_message = _("hidden")
        elif time_place.publication_time > timezone.now():
            unpublished_message = _("future publication time")
        else:
            return _("Yes")

        no_translation = _("No")
        return f"{no_translation} ({unpublished_message})"

    @admin.display(description=_("active tickets"))
    def get_active_tickets(self, time_place: TimePlace):
        return get_ticket_table(time_place.tickets.filter(active=True))

    @admin.display(description=_("inactive tickets"))
    def get_inactive_tickets(self, time_place: TimePlace):
        return get_ticket_table(time_place.tickets.filter(active=False))

    def get_search_results(self, request, queryset, search_term):
        return search_escaped_and_unescaped(super(), request, queryset, search_term)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(ticket_count=Count('tickets', filter=Q(tickets__active=True)))  # facilitates querying `ticket_count`


admin.site.register(Article, ArticleAdmin)
admin.site.register(Event, EventAdmin)
admin.site.register(TimePlace, TimePlaceAdmin)
admin.site.register(EventTicket)
