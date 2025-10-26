from abc import ABC
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from django_hosts import reverse

from news.models import Article, Event, EventTicket, TimePlace
from users.models import User
from util.test_utils import (
    CleanUpTempFilesTestMixin,
    Get,
    MOCK_JPG_FILE,
    assert_requesting_paths_succeeds,
    generate_all_admin_urls_for_model_and_objs,
)


class NewsTestBase(CleanUpTempFilesTestMixin, ABC):
    # noinspection PyAttributeOutsideInit
    def init_objs(self):
        self.article1 = Article.objects.create(
            title="Article 1",
            content="Lorem ipsum dolor sit amet",
            clickbait="Pleeasee!",
            image=MOCK_JPG_FILE,
            image_description="Mock image",
            featured=True,
            hidden=False,
            private=False,
        )
        self.article2 = Article.objects.create(
            title="Article 2",
            content="You will not believe...",
            clickbait="Or..?!",
            image=MOCK_JPG_FILE,
            image_description="Mock image",
            private=True,
        )

        self.event1 = Event.objects.create(
            title="Event 1",
            content="Lorem ipsum dolor sit amet",
            clickbait="Join us!",
            image=MOCK_JPG_FILE,
            image_description="Mock image",
            featured=True,
        )
        self.event2 = Event.objects.create(
            title="Event 2",
            content="Lorem ipsum electric boogaloo",
            clickbait="Do it!",
            image=MOCK_JPG_FILE,
            image_description="Mock image",
            private=True,
            event_type=Event.Type.STANDALONE,
            number_of_tickets=3,
        )
        now = timezone.localtime()
        self.time_place1 = TimePlace.objects.create(
            event=self.event1,
            start_time=now,
            end_time=now + timedelta(hours=3),
            place="Makerverkstedet",
            place_url="https://makentnu.no/",
            hidden=False,
            number_of_tickets=5,
        )
        self.time_place2 = TimePlace.objects.create(
            event=self.event1,
            start_time=now + timedelta(days=1),
            end_time=now + timedelta(days=1, hours=3),
            place="U1",
            place_url="https://www.ntnu.no/ub/bibliotek/real",
            hidden=False,
            number_of_tickets=5,
        )
        self.time_place3 = TimePlace.objects.create(
            event=self.event2,
            start_time=now,
            end_time=now + timedelta(hours=12),
            place="Home",
            place_url="http://makentnu.localhost:8000/",
            hidden=False,
        )
        self.time_places = (self.time_place1, self.time_place2, self.time_place3)

        self.user1 = User.objects.create_user(username="user1")
        self.user2 = User.objects.create_user(
            username="user2", first_name="Hey", last_name="It's Me"
        )

        self.ticket1 = EventTicket.objects.create(
            user=self.user1,
            timeplace=self.time_place1,
            comment="Looking forward to this!!",
            language=EventTicket.Language.ENGLISH,
        )
        self.ticket2 = EventTicket.objects.create(
            user=self.user2,
            timeplace=self.time_place1,
            comment="~Woop~",
            language=EventTicket.Language.NORWEGIAN,
        )
        self.ticket3 = EventTicket.objects.create(
            user=self.user1,
            timeplace=self.time_place2,
            active=False,
            language=EventTicket.Language.ENGLISH,
        )
        self.ticket4 = EventTicket.objects.create(
            user=self.user2,
            timeplace=self.time_place2,
            active=True,
            language=EventTicket.Language.ENGLISH,
        )
        self.ticket5 = EventTicket.objects.create(
            user=self.user1,
            timeplace=self.time_place3,
            language=EventTicket.Language.NORWEGIAN,
        )
        self.tickets = (
            self.ticket1,
            self.ticket2,
            self.ticket3,
            self.ticket4,
            self.ticket5,
        )
        self.active_tickets = (self.ticket1, self.ticket2, self.ticket4, self.ticket5)


class UrlTests(NewsTestBase, TestCase):
    def setUp(self):
        self.init_objs()

    def test_all_get_request_paths_succeed(self):
        path_predicates = [
            # article_urlpatterns
            Get(reverse("article_list"), public=True),
            Get(reverse("article_detail", args=[self.article1.pk]), public=True),
            Get(  # This article is private
                reverse("article_detail", args=[self.article2.pk]), public=False
            ),
            # specific_time_place_urlpatterns
            Get(reverse("event_ticket_create", args=[self.event1.pk]), public=False),
            Get(reverse("event_ticket_create", args=[self.event2.pk]), public=False),
            *[
                Get(
                    reverse(
                        "time_place_ical", args=[time_place.event.pk, time_place.pk]
                    ),
                    public=True,
                )
                for time_place in self.time_places
            ],
            # specific_event_urlpatterns
            Get(reverse("event_detail", args=[self.event1.pk]), public=True),
            Get(  # This event is private
                reverse("event_detail", args=[self.event2.pk]), public=False
            ),
            *[
                Get(
                    reverse(
                        "event_ticket_create", args=[time_place.event.pk, time_place.pk]
                    ),
                    public=False,
                )
                for time_place in self.time_places
                # Can't test `time_place3`, as it has no tickets
                if time_place != self.time_place3
            ],
            # event_urlpatterns
            Get(reverse("event_list"), public=True),
            # specific_ticket_urlpatterns
            *[
                Get(reverse("event_ticket_detail", args=[ticket.pk]), public=False)
                for ticket in self.tickets
            ],
            *[
                Get(reverse("event_ticket_cancel", args=[ticket.pk]), public=False)
                for ticket in self.active_tickets
            ],
            # ticket_urlpatterns
            Get(reverse("event_ticket_my_list"), public=False),
            # specific_article_adminpatterns
            Get(reverse("article_update", args=[self.article1.pk]), public=False),
            Get(reverse("article_update", args=[self.article2.pk]), public=False),
            # article_adminpatterns
            Get(reverse("admin_article_list"), public=False),
            Get(reverse("article_create"), public=False),
            # specific_time_place_adminpatterns
            *[
                Get(
                    reverse(
                        "time_place_update", args=[time_place.event.pk, time_place.pk]
                    ),
                    public=False,
                )
                for time_place in self.time_places
            ],
            *[
                Get(
                    reverse(
                        "admin_time_place_ticket_list",
                        args=[time_place.event.pk, time_place.pk],
                    ),
                    public=False,
                )
                for time_place in self.time_places
                # Can't test `time_place3`, as it has no tickets
                if time_place != self.time_place3
            ],
            # time_place_adminpatterns
            Get(reverse("time_place_create", args=[self.event1.pk]), public=False),
            Get(reverse("time_place_create", args=[self.event2.pk]), public=False),
            # specific_event_adminpatterns
            Get(reverse("admin_event_detail", args=[self.event1.pk]), public=False),
            Get(reverse("admin_event_detail", args=[self.event2.pk]), public=False),
            Get(reverse("event_update", args=[self.event1.pk]), public=False),
            Get(reverse("event_update", args=[self.event2.pk]), public=False),
            Get(  # Can't test `event1`, as it has no tickets
                reverse("admin_event_ticket_list", args=[self.event2.pk]), public=False
            ),
            # event_adminpatterns
            Get(reverse("admin_event_list"), public=False),
            Get(reverse("event_create"), public=False),
            Get(reverse("admin_event_participants_search"), public=False),
            Get(
                f"{reverse('admin_event_participants_search')}?search_string={self.user1.username}",
                public=False,
            ),
            Get(
                f"{reverse('admin_event_participants_search')}?search_string={self.user2.get_full_name()}",
                public=False,
            ),
            Get(
                f"{reverse('admin_event_participants_search')}?search_string=stringthatdoesntmatchanything",
                public=False,
            ),
        ]
        assert_requesting_paths_succeeds(self, path_predicates)

    def test_all_admin_get_request_paths_succeed(self):
        path_predicates = [
            *[
                Get(admin_url, public=False)
                for admin_url in generate_all_admin_urls_for_model_and_objs(
                    Article, [self.article1, self.article2]
                )
            ],
            *[
                Get(admin_url, public=False)
                for admin_url in generate_all_admin_urls_for_model_and_objs(
                    EventTicket, self.tickets
                )
            ],
            *[
                Get(admin_url, public=False)
                for admin_url in generate_all_admin_urls_for_model_and_objs(
                    Event, [self.event1, self.event2]
                )
            ],
            *[
                Get(admin_url, public=False)
                for admin_url in generate_all_admin_urls_for_model_and_objs(
                    TimePlace, self.time_places
                )
            ],
        ]
        assert_requesting_paths_succeeds(self, path_predicates, "admin")
