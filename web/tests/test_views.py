from datetime import datetime, timedelta
from http import HTTPStatus
from typing import List

from django.test import Client, TestCase
from django.utils import timezone
from django_hosts import reverse

from news.models import Event, TimePlace
from users.models import User
from util.test_utils import CleanUpTempFilesTestMixin, MOCK_JPG_FILE, assertRedirectsWithPathPrefix
from web.views import IndexView


class IndexViewTests(CleanUpTempFilesTestMixin, TestCase):

    def setUp(self):
        self.path = reverse('front_page')

    @staticmethod
    def create_time_place(*, start_time: datetime, event: Event) -> TimePlace:
        return TimePlace.objects.create(
            event=event, start_time=start_time, end_time=start_time + timedelta(hours=2),
            place="Makerverkstedet", place_url="https://makentnu.no/", hidden=False,
        )

    @classmethod
    def create_event(cls, *, event_type: Event.Type, private=False) -> Event:
        num_existing_events = Event.objects.count()
        return Event.objects.create(
            title=f"Event {num_existing_events + 1}", content="Lorem ipsum dolor sit amet.", clickbait="!!!", image=MOCK_JPG_FILE,
            featured=True, private=private, event_type=event_type,
        )

    @classmethod
    def create_event_with_one_time_place(cls, *, event_type: Event.Type, start_time: datetime, private=False) -> Event:
        event = cls.create_event(event_type=event_type, private=private)
        cls.create_time_place(start_time=start_time, event=event)
        return event

    def get_response_context(self, client: Client = None) -> dict:
        client = client or self.client
        return client.get(self.path).context

    def test_context_data_contains_expected_event_dict_values(self):
        def assert_context_event_dicts_equal(expected_event_dicts: List[dict]):
            response_context = self.get_response_context()
            self.assertListEqual(response_context['featured_event_dicts'], expected_event_dicts)

        now = timezone.now()

        # Events with no time places should not be shown
        empty_standalone = self.create_event(event_type=Event.Type.STANDALONE)
        empty_repeating = self.create_event(event_type=Event.Type.REPEATING)
        assert_context_event_dicts_equal([])

        # Events with only past time places should not be shown
        past_standalone = self.create_event(event_type=Event.Type.STANDALONE)
        self.create_time_place(start_time=now - timedelta(days=1), event=past_standalone)
        past_repeating = self.create_event(event_type=Event.Type.REPEATING)
        self.create_time_place(start_time=now - timedelta(days=1), event=past_repeating)
        assert_context_event_dicts_equal([])

        # Events with future time places should be shown, even if they also have past time places
        future_standalone = self.create_event(event_type=Event.Type.STANDALONE)
        future_standalone__past = self.create_time_place(start_time=now + timedelta(days=-2), event=future_standalone)
        future_standalone__2_days = self.create_time_place(start_time=now + timedelta(days=2), event=future_standalone)
        future_repeating = self.create_event(event_type=Event.Type.REPEATING)
        future_repeating__past = self.create_time_place(start_time=now + timedelta(days=-3), event=future_repeating)
        future_repeating__3_days = self.create_time_place(start_time=now + timedelta(days=3), event=future_repeating)
        future_standalone_dict = {
            'event': future_standalone,
            'shown_occurrence': future_standalone__2_days,
            'number_of_occurrences': 2,
        }
        future_repeating_dict = {
            'event': future_repeating,
            'shown_occurrence': future_repeating__3_days,
            'number_of_occurrences': 1,
        }
        assert_context_event_dicts_equal([future_standalone_dict, future_repeating_dict])

        # Adding a time place that occurs before the existing future ones,
        # should change the first occurrence, and make the associated event be listed first
        future_repeating__1_day = self.create_time_place(start_time=now + timedelta(days=1), event=future_repeating)
        future_repeating_dict['shown_occurrence'] = future_repeating__1_day
        future_repeating_dict['number_of_occurrences'] = 2
        assert_context_event_dicts_equal([future_repeating_dict, future_standalone_dict])

        # Adding a time place that occurs between the two existing ones for that event, should not change the first occurrence
        future_repeating__2_days = self.create_time_place(start_time=now + timedelta(days=2), event=future_repeating)
        future_repeating_dict['number_of_occurrences'] = 3
        assert_context_event_dicts_equal([future_repeating_dict, future_standalone_dict])

    def test_context_data_contains_expected_events(self):
        now = timezone.now()

        # No events to begin with
        response_context = self.get_response_context()
        self.assertEqual(Event.objects.count(), 0)
        self.assertEqual(len(response_context['featured_event_dicts']), 0)
        self.assertFalse(response_context['more_events_exist'])

        # Create events in chronological order, up until the max shown events limit
        ordered_events = []
        self.assertEqual(IndexView.MAX_EVENTS_SHOWN, 4)
        for event_num in range(1, IndexView.MAX_EVENTS_SHOWN + 1):
            with self.subTest(event_num=event_num):
                event = self.create_event_with_one_time_place(event_type=Event.Type.STANDALONE, start_time=now + timedelta(days=event_num))
                ordered_events.append(event)

                response_context = self.get_response_context()
                response_event_dicts = response_context['featured_event_dicts']
                self.assertEqual(len(response_event_dicts), event_num)
                self.assertListEqual(
                    [event_dict['event'] for event_dict in response_event_dicts],
                    ordered_events,
                )
                self.assertFalse(response_context['more_events_exist'])

        # Create one more event before the existing ones, which should not change the number of events shown,
        # and should make the "More events" button visible
        event = self.create_event_with_one_time_place(event_type=Event.Type.STANDALONE, start_time=now + timedelta(days=0.5))
        response_context = self.get_response_context()
        response_event_dicts = response_context['featured_event_dicts']
        self.assertEqual(Event.objects.count(), IndexView.MAX_EVENTS_SHOWN + 1)
        self.assertEqual(len(response_event_dicts), IndexView.MAX_EVENTS_SHOWN)
        self.assertEqual(response_event_dicts[0]['event'], event)
        self.assertTrue(response_context['more_events_exist'])

    def test_context_data_contains_expected_private_events(self):
        now = timezone.now()
        internal_user = User.objects.create_user(username="internal_user")
        internal_user.add_perms('news.can_view_private')
        internal_client = Client()
        internal_client.force_login(internal_user)

        public_event = self.create_event_with_one_time_place(event_type=Event.Type.STANDALONE, start_time=now + timedelta(days=1), private=False)
        private_event = self.create_event_with_one_time_place(event_type=Event.Type.STANDALONE, start_time=now + timedelta(days=2), private=True)

        # Unauthorized client can only see public event
        response_event_dicts = self.get_response_context(self.client)['event_dicts']
        self.assertEqual(len(response_event_dicts), 1)
        self.assertEqual(response_event_dicts[0]['event'], public_event)

        # Internal client can see both the public and the private event
        response_event_dicts = self.get_response_context(internal_client)['event_dicts']
        self.assertEqual(len(response_event_dicts), 2)
        self.assertEqual(response_event_dicts[0]['event'], public_event)
        self.assertEqual(response_event_dicts[1]['event'], private_event)


class AdminPanelViewTests(TestCase):

    def setUp(self):
        self.path = reverse('adminpanel')

    def test_only_users_with_required_permissions_can_view_page(self):
        def assert_visiting_page_produces_status_code(expected_status_code: int):
            response = self.client.get(self.path)
            if expected_status_code == HTTPStatus.FOUND:
                assertRedirectsWithPathPrefix(self, response, "/login/")
            else:
                self.assertEqual(response.status_code, expected_status_code)

        assert_visiting_page_produces_status_code(HTTPStatus.FOUND)

        user = User.objects.create_user(username="user")
        self.client.force_login(user)
        assert_visiting_page_produces_status_code(HTTPStatus.FORBIDDEN)

        user.add_perms('news.add_article')
        assert_visiting_page_produces_status_code(HTTPStatus.OK)
