from abc import ABC
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from django_hosts import reverse

from news.models import Article, Event, EventTicket, TimePlace
from users.models import User
from util.test_utils import (
    CleanUpTempFilesTestMixin, Get, MOCK_JPG_FILE, assert_requesting_paths_succeeds, generate_all_admin_urls_for_model_and_objs,
)


class NewsTestBase(CleanUpTempFilesTestMixin, ABC):

    # noinspection PyAttributeOutsideInit
    def init_objs(self):
        self.article1 = Article.objects.create(
            title="Article 1", content="Lorem ipsum dolor sit amet", clickbait="Pleeasee!", image=MOCK_JPG_FILE, image_description="Mock image",
            featured=True, hidden=False, private=False,
        )
        self.article2 = Article.objects.create(
            title="Article 2", content="You will not believe...", clickbait="Or..?!", image=MOCK_JPG_FILE, image_description="Mock image",
            private=True,
        )

        self.event1 = Event.objects.create(
            title="Event 1", content="Lorem ipsum dolor sit amet", clickbait="Join us!", image=MOCK_JPG_FILE, image_description="Mock image",
            featured=True,
        )
        self.event2 = Event.objects.create(
            title="Event 2", content="Lorem ipsum electric boogaloo", clickbait="Do it!", image=MOCK_JPG_FILE, image_description="Mock image",
            private=True, event_type=Event.Type.STANDALONE, number_of_tickets=3,
        )
        now = timezone.localtime()
        self.time_place1 = TimePlace.objects.create(
            event=self.event1, start_time=now, end_time=now + timedelta(hours=3),
            place="Makerverkstedet", place_url="https://makentnu.no/", hidden=False, number_of_tickets=5,
        )
        self.time_place2 = TimePlace.objects.create(
            event=self.event1, start_time=now + timedelta(days=1), end_time=now + timedelta(days=1, hours=3),
            place="U1", place_url="https://www.ntnu.no/ub/bibliotek/real", hidden=False, number_of_tickets=5,
        )
        self.time_place3 = TimePlace.objects.create(
            event=self.event2, start_time=now, end_time=now + timedelta(hours=12),
            place="Home", place_url="http://makentnu.localhost:8000/", hidden=False,
        )
        self.time_places = (self.time_place1, self.time_place2, self.time_place3)

        self.user1 = User.objects.create_user(username="user1")
        self.user2 = User.objects.create_user(username="user2")

        self.ticket1 = EventTicket.objects.create(
            user=self.user1, timeplace=self.time_place1, comment="Looking forward to this!!", language=EventTicket.Language.ENGLISH,
        )
        self.ticket2 = EventTicket.objects.create(
            user=self.user2, timeplace=self.time_place1, comment="~Woop~", language=EventTicket.Language.NORWEGIAN,
        )
        self.ticket3 = EventTicket.objects.create(
            user=self.user1, timeplace=self.time_place2, active=False, language=EventTicket.Language.ENGLISH,
        )
        self.ticket4 = EventTicket.objects.create(
            user=self.user2, timeplace=self.time_place2, active=True, language=EventTicket.Language.ENGLISH,
        )
        self.ticket5 = EventTicket.objects.create(
            user=self.user1, timeplace=self.time_place3, language=EventTicket.Language.NORWEGIAN,
        )
        self.tickets = (self.ticket1, self.ticket2, self.ticket3, self.ticket4, self.ticket5)


class UrlTests(NewsTestBase, TestCase):

    def setUp(self):
        self.init_objs()

    def test_all_get_request_paths_succeed(self):
        path_predicates = [
            Get(reverse('admin_article_list'), public=False),
            Get(reverse('admin_event_list'), public=False),
            Get(reverse('admin_event_detail', kwargs={'event': self.event1}), public=False),
            Get(reverse('admin_event_detail', kwargs={'event': self.event2}), public=False),
            Get(reverse('article_list'), public=True),
            Get(reverse('article_create'), public=False),
            Get(reverse('article_edit', kwargs={'article': self.article1}), public=False),
            Get(reverse('article_edit', kwargs={'article': self.article2}), public=False),
            Get(reverse('article_detail', kwargs={'article': self.article1}), public=True),
            Get(reverse('article_detail', kwargs={'article': self.article2}), public=False),  # this article is private
            Get(reverse('event_list'), public=True),
            Get(reverse('event_create'), public=False),
            Get(reverse('event_edit', kwargs={'event': self.event1}), public=False),
            Get(reverse('event_edit', kwargs={'event': self.event2}), public=False),
            Get(reverse('event_ticket_list', kwargs={'event': self.event2}), public=False),  # can't test `event1`, as it has no tickets
            Get(reverse('event_detail', kwargs={'event': self.event1}), public=True),
            Get(reverse('event_detail', kwargs={'event': self.event2}), public=False),  # this event is private
            Get(reverse('register_event', kwargs={'event': self.event1}), public=False),
            Get(reverse('register_event', kwargs={'event': self.event2}), public=False),
            *[
                Get(reverse('timeplace_edit', kwargs={'event': time_place.event, 'pk': time_place.pk}), public=False)
                for time_place in self.time_places
            ],
            Get(reverse('timeplace_create', kwargs={'event': self.event1}), public=False),
            Get(reverse('timeplace_create', kwargs={'event': self.event2}), public=False),
            *[
                Get(reverse('timeplace_ticket_list', kwargs={'event': time_place.event, 'pk': time_place.pk}), public=False)
                for time_place in self.time_places if time_place != self.time_place3  # can't test `time_place3`, as it has no tickets
            ],
            *[
                Get(reverse('timeplace_ical', kwargs={'event': time_place.event, 'pk': time_place.pk}), public=True)
                for time_place in self.time_places
            ],
            *[
                Get(reverse('register_timeplace', kwargs={'event': time_place.event, 'time_place_pk': time_place.pk}), public=False)
                for time_place in self.time_places if time_place != self.time_place3  # can't test `time_place3`, as it has no tickets
            ],
            *[
                Get(reverse('ticket_detail', kwargs={'pk': ticket.pk}), public=False)
                for ticket in self.tickets
            ],
            Get(reverse('my_tickets_list'), public=False),
        ]
        assert_requesting_paths_succeeds(self, path_predicates)

    def test_all_admin_get_request_paths_succeed(self):
        path_predicates = [
            *[
                Get(admin_url, public=False)
                for admin_url in generate_all_admin_urls_for_model_and_objs(Article, [self.article1, self.article2])
            ],
            *[
                Get(admin_url, public=False)
                for admin_url in generate_all_admin_urls_for_model_and_objs(EventTicket, self.tickets)
            ],
            *[
                Get(admin_url, public=False)
                for admin_url in generate_all_admin_urls_for_model_and_objs(Event, [self.event1, self.event2])
            ],
            *[
                Get(admin_url, public=False)
                for admin_url in generate_all_admin_urls_for_model_and_objs(TimePlace, self.time_places)
            ],
        ]
        assert_requesting_paths_succeeds(self, path_predicates, 'admin')
