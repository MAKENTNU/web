from django.conf import settings
from django_ical.views import ICalFeed

from .models import TimePlace


class EventFeed(ICalFeed):
    """An iCal feed of all the events available to the user."""

    file_name = "events.ics"
    timezone = settings.TIME_ZONE

    def get_object(self, request, *args, **kwargs):
        return {
            "user_can_view_private": request.user.has_perm("news.can_view_private"),
            "query_kwargs": {},
        }

    def items(self, attrs):
        items = TimePlace.objects.all()

        if attrs["query_kwargs"]:
            items = items.filter(**attrs["query_kwargs"])

        if not attrs["user_can_view_private"]:
            items = items.filter(event__private=False)

        return items

    def item_link(self, item: TimePlace):
        return item.event.get_absolute_url()

    def item_title(self, item: TimePlace):
        return item.event.title

    def item_description(self, item: TimePlace):
        return item.event.clickbait

    def item_start_datetime(self, item: TimePlace):
        return item.start_time

    def item_end_datetime(self, item: TimePlace):
        return item.end_time

    def item_location(self, item: TimePlace):
        return item.place

    def product_id(self):
        return "MAKE NTNU"


class SingleEventFeed(EventFeed):
    """An iCal feed of all occurrences of a single event."""

    def file_name(self, attrs):
        title = self.items(attrs).values_list("event__title", flat=True).first()
        return f"{title}.ics"

    def get_object(self, request, *args, **kwargs):
        attrs = super().get_object(request, *args, **kwargs)
        attrs["query_kwargs"]["event_id"] = int(kwargs["pk"])

        return attrs


class SingleTimePlaceFeed(EventFeed):
    """An iCal feed of a single occurrences of an event."""

    def file_name(self, attrs):
        title = self.items(attrs).values_list("event__title", flat=True).first()
        return f"{title}.ics"

    def get_object(self, request, *args, **kwargs):
        attrs = super().get_object(request, *args, **kwargs)
        attrs["query_kwargs"]["id"] = int(kwargs["time_place_pk"])

        return attrs
