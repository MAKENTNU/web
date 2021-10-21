from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from django_hosts import reverse

from news.models import Article, Event, EventTicket, TimePlace
from users.models import User
from util.test_utils import Get, MOCK_JPG_FILE, assert_requesting_paths_succeeds


class UrlTests(TestCase):

    @staticmethod
    def init_objs(self: TestCase):
        self.article1 = Article.objects.create(
            title="Article 1", content="Lorem ipsum dolor sit amet", clickbait="Pleeasee!", image=MOCK_JPG_FILE,
            featured=True, hidden=False, private=False,
        )
        self.article2 = Article.objects.create(
            title="Article 2", content="You will not believe...", clickbait="Or..?!", image=MOCK_JPG_FILE, private=True,
        )

        self.event1 = Event.objects.create(
            title="Event 1", content="Lorem ipsum dolor sit amet", clickbait="Join us!", image=MOCK_JPG_FILE, featured=True,
        )
        self.event2 = Event.objects.create(
            title="Event 2", content="Lorem ipsum electric boogaloo", clickbait="Do it!", image=MOCK_JPG_FILE, private=True,
            event_type=Event.Type.STANDALONE, number_of_tickets=3,
        )
        now = timezone.localtime()
        self.timeplace1 = TimePlace.objects.create(
            event=self.event1, start_time=now, end_time=now + timedelta(hours=3),
            place="Makerverkstedet", place_url="https://makentnu.no/", hidden=False, number_of_tickets=5,
        )
        self.timeplace2 = TimePlace.objects.create(
            event=self.event1, start_time=now + timedelta(days=1), end_time=now + timedelta(days=1, hours=3),
            place="U1", place_url="https://www.ntnu.no/ub/bibliotek/real", hidden=False, number_of_tickets=5,
        )
        self.timeplace3 = TimePlace.objects.create(
            event=self.event2, start_time=now, end_time=now + timedelta(hours=12),
            place="Home", place_url="http://makentnu.localhost:8000/", hidden=False,
        )
        self.timeplaces = (self.timeplace1, self.timeplace2, self.timeplace3)

        self.user1 = User.objects.create_user(username="user1")
        self.user2 = User.objects.create_user(username="user2")

        self.ticket1 = EventTicket.objects.create(
            user=self.user1, timeplace=self.timeplace1, comment="Looking forward to this!!", language=EventTicket.Language.ENGLISH,
        )
        self.ticket2 = EventTicket.objects.create(
            user=self.user2, timeplace=self.timeplace1, comment="~Woop~", language=EventTicket.Language.NORWEGIAN,
        )
        self.ticket3 = EventTicket.objects.create(
            user=self.user1, timeplace=self.timeplace2, active=False, language=EventTicket.Language.ENGLISH,
        )
        self.ticket4 = EventTicket.objects.create(
            user=self.user2, timeplace=self.timeplace2, active=True, language=EventTicket.Language.ENGLISH,
        )
        self.ticket5 = EventTicket.objects.create(
            user=self.user1, timeplace=self.timeplace3, language=EventTicket.Language.NORWEGIAN,
        )
        self.tickets = (self.ticket1, self.ticket2, self.ticket3, self.ticket4, self.ticket5)

    def setUp(self):
        self.init_objs(self)

    def test_all_get_request_paths_succeed(self):
        path_predicates = [
            Get(reverse('admin_article_list'), public=False),
            Get(reverse('admin_event_list'), public=False),
            Get(reverse('admin_event_detail', kwargs={'pk': self.event1.pk}), public=False),
            Get(reverse('admin_event_detail', kwargs={'pk': self.event2.pk}), public=False),
            Get(reverse('article_list'), public=True),
            Get(reverse('article_create'), public=False),
            Get(reverse('article_edit', kwargs={'pk': self.article1.pk}), public=False),
            Get(reverse('article_edit', kwargs={'pk': self.article2.pk}), public=False),
            Get(reverse('article_detail', kwargs={'pk': self.article1.pk}), public=True),
            Get(reverse('article_detail', kwargs={'pk': self.article2.pk}), public=False),  # this article is private
            Get(reverse('event_list'), public=True),
            Get(reverse('event_create'), public=False),
            Get(reverse('event_edit', kwargs={'pk': self.event1.pk}), public=False),
            Get(reverse('event_edit', kwargs={'pk': self.event2.pk}), public=False),
            Get(reverse('event_ticket_list', kwargs={'pk': self.event2.pk}), public=False),  # can't test `event1`, as it has no tickets
            Get(reverse('event_detail', kwargs={'pk': self.event1.pk}), public=True),
            Get(reverse('event_detail', kwargs={'pk': self.event2.pk}), public=False),  # this event is private
            Get(reverse('register_event', kwargs={'event_pk': self.event1.pk}), public=False),
            Get(reverse('register_event', kwargs={'event_pk': self.event2.pk}), public=False),
            *[
                Get(reverse('timeplace_edit', kwargs={'pk': timeplace.pk}), public=False)
                for timeplace in self.timeplaces
            ],
            Get(reverse('timeplace_create', kwargs={'event_pk': self.event1.pk}), public=False),
            Get(reverse('timeplace_create', kwargs={'event_pk': self.event2.pk}), public=False),
            *[
                Get(reverse('timeplace_ticket_list', kwargs={'pk': timeplace.pk}), public=False)
                for timeplace in self.timeplaces if timeplace != self.timeplace3  # can't test `timeplace3`, as it has no tickets
            ],
            *[
                Get(reverse('timeplace_ical', kwargs={'pk': timeplace.pk}), public=True)
                for timeplace in self.timeplaces
            ],
            *[
                Get(reverse('register_timeplace', kwargs={'timeplace_pk': timeplace.pk}), public=False)
                for timeplace in self.timeplaces if timeplace != self.timeplace3  # can't test `timeplace3`, as it has no tickets
            ],
            *[
                Get(reverse('ticket_detail', kwargs={'pk': ticket.pk}), public=False)
                for ticket in self.tickets
            ],
            Get(reverse('my_tickets_list'), public=False),
        ]
        assert_requesting_paths_succeeds(self, path_predicates)
