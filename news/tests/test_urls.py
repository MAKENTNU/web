from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from django_hosts import reverse

from news.models import Article, Event, EventTicket, TimePlace
from users.models import User
from util.test_utils import MOCK_JPG_FILE, assert_requesting_paths_succeeds


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

        self.user1 = User.objects.create(username="user1")
        self.user2 = User.objects.create(username="user2")

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
        paths_to_must_be_authenticated = {
            reverse('admin-articles'): True,
            reverse('admin-events'): True,
            reverse('admin-event', kwargs={'pk': self.event1.pk}): True,
            reverse('admin-event', kwargs={'pk': self.event2.pk}): True,
            reverse('articles'): False,
            reverse('article-create'): True,
            reverse('article-edit', kwargs={'pk': self.article1.pk}): True,
            reverse('article-edit', kwargs={'pk': self.article2.pk}): True,
            reverse('article', kwargs={'pk': self.article1.pk}): False,
            reverse('article', kwargs={'pk': self.article2.pk}): True,  # this article is private
            reverse('events'): False,
            reverse('event-create'): True,
            reverse('event-edit', kwargs={'pk': self.event1.pk}): True,
            reverse('event-edit', kwargs={'pk': self.event2.pk}): True,
            reverse('event-tickets', kwargs={'pk': self.event2.pk}): True,  # can't test `event1`, as it has no tickets
            reverse('event', kwargs={'pk': self.event1.pk}): False,
            reverse('event', kwargs={'pk': self.event2.pk}): True,  # this event is private
            reverse('register-event', kwargs={'event_pk': self.event1.pk}): True,
            reverse('register-event', kwargs={'event_pk': self.event2.pk}): True,
            **{
                reverse('timeplace-edit', kwargs={'pk': timeplace.pk}): True
                for timeplace in self.timeplaces
            },
            reverse('timeplace-new', kwargs={'event_pk': self.event1.pk}): True,
            reverse('timeplace-new', kwargs={'event_pk': self.event2.pk}): True,
            **{
                reverse('timeplace-tickets', kwargs={'pk': timeplace.pk}): True
                for timeplace in self.timeplaces if timeplace != self.timeplace3  # can't test `timeplace3`, as it has no tickets
            },
            **{
                reverse('timeplace-ical', kwargs={'pk': timeplace.pk}): False
                for timeplace in self.timeplaces
            },
            **{
                reverse('register-timeplace', kwargs={'timeplace_pk': timeplace.pk}): True
                for timeplace in self.timeplaces if timeplace != self.timeplace3  # can't test `timeplace3`, as it has no tickets
            },
            **{
                reverse('ticket', kwargs={'pk': ticket.uuid}): True
                for ticket in self.tickets
            },
            reverse('my-tickets'): True,
        }
        assert_requesting_paths_succeeds(self, paths_to_must_be_authenticated)
