from datetime import timedelta
from http import HTTPStatus
from typing import Optional
from urllib.parse import urlparse

from django.test import Client, TestCase
from django.utils import timezone
from django_hosts import reverse

from users.models import User
from util.model_utils import duplicate
from ...models import Event, EventTicket, TimePlace


class TestEventTicketViews(TestCase):

    def setUp(self):
        now = timezone.localtime()

        self.repeating_event = Event.objects.create(title="Repeating event", event_type=Event.Type.REPEATING)
        self.repeating_time_place = TimePlace.objects.create(
            event=self.repeating_event, start_time=now, end_time=now + timedelta(hours=1), hidden=False,
            number_of_tickets=10,
        )

        self.standalone_event = Event.objects.create(title="Standalone event", event_type=Event.Type.STANDALONE, number_of_tickets=10)
        self.standalone_time_place = TimePlace.objects.create(
            event=self.standalone_event, start_time=now, end_time=now + timedelta(hours=1), hidden=False,
        )

        self.user1 = User.objects.create_user(username="user1")
        self.client1 = Client()
        self.client1.force_login(self.user1)

    def test__event_registration_view__can_only_be_viewed_with_correct_url_for_event_type(self):
        def assert_response_status_code(url: str, status_code: int):
            response = self.client1.get(url)
            self.assertEqual(response.status_code, status_code)

        assert_response_status_code(reverse('register_event', args=[self.repeating_event.pk]), HTTPStatus.FORBIDDEN)
        assert_response_status_code(reverse('register_timeplace', args=[self.repeating_event.pk, self.repeating_time_place.pk]), HTTPStatus.OK)
        assert_response_status_code(reverse('register_event', args=[self.standalone_event.pk]), HTTPStatus.OK)
        assert_response_status_code(reverse('register_timeplace', args=[self.standalone_event.pk, self.standalone_time_place.pk]), HTTPStatus.FORBIDDEN)

    def test__event_registration_view__can_only_be_viewed_with_correct_combination_of_event_and_time_place(self):
        repeating_event1 = self.repeating_event
        repeating_event2 = duplicate(self.repeating_event)
        repeating_time_place1 = self.repeating_time_place
        repeating_time_place2 = duplicate(self.repeating_time_place, event=repeating_event2)

        def assert_response_status_code(url_args: list, status_code: int):
            url = reverse('register_timeplace', args=url_args)
            response = self.client1.get(url)
            self.assertEqual(response.status_code, status_code)

        assert_response_status_code([repeating_event1.pk, repeating_time_place1.pk], HTTPStatus.OK)
        assert_response_status_code([repeating_event1.pk, repeating_time_place2.pk], HTTPStatus.NOT_FOUND)
        assert_response_status_code([repeating_event1.pk, self.standalone_time_place.pk], HTTPStatus.NOT_FOUND)
        assert_response_status_code([repeating_event2.pk, repeating_time_place1.pk], HTTPStatus.NOT_FOUND)
        assert_response_status_code([repeating_event2.pk, repeating_time_place2.pk], HTTPStatus.OK)
        assert_response_status_code([repeating_event2.pk, self.standalone_time_place.pk], HTTPStatus.NOT_FOUND)
        assert_response_status_code([self.standalone_event.pk, repeating_time_place1.pk], HTTPStatus.NOT_FOUND)
        assert_response_status_code([self.standalone_event.pk, repeating_time_place2.pk], HTTPStatus.NOT_FOUND)
        assert_response_status_code([self.standalone_event.pk, self.standalone_time_place.pk], HTTPStatus.FORBIDDEN)

    def test__event_registration_view__creates_and_reactivates_tickets_as_expected(self):
        for time_place_or_event in [self.repeating_time_place, self.standalone_event]:
            with self.subTest(time_place_or_event=time_place_or_event):
                if isinstance(time_place_or_event, TimePlace):
                    registration_url = reverse('register_timeplace', args=[time_place_or_event.event.pk, time_place_or_event.pk])
                else:
                    registration_url = reverse('register_event', args=[time_place_or_event.pk])

                self.assertEqual(time_place_or_event.tickets.count(), 0)

                def assert_results_after_registering_for_event(posted_data: dict, *, expected_form_instance: Optional[EventTicket],
                                                               expected_language: str, expected_comment: str) -> EventTicket:
                    form_instance = self.client1.get(registration_url).context['form'].instance
                    if expected_form_instance:
                        self.assertEqual(form_instance, expected_form_instance)
                    else:
                        self.assertFalse(EventTicket.objects.filter(pk=form_instance.pk).exists())

                    response = self.client1.post(registration_url, posted_data)

                    self.assertEqual(time_place_or_event.tickets.count(), 1)
                    ticket = time_place_or_event.tickets.get()

                    ticket_detail_url = urlparse(reverse('ticket_detail', args=[ticket.pk])).path
                    self.assertRedirects(response, ticket_detail_url)

                    self.assertEqual(ticket.language, expected_language)
                    self.assertEqual(ticket.comment, expected_comment)
                    self.assertTrue(ticket.active)
                    return ticket

                created_ticket = assert_results_after_registering_for_event(
                    {'language': 'nb'},
                    expected_form_instance=None, expected_language='nb', expected_comment="",
                )

                created_ticket.active = False
                created_ticket.save()

                assert_results_after_registering_for_event(
                    {'language': 'en', 'comment': "A comment :)"},
                    expected_form_instance=created_ticket, expected_language='en', expected_comment="A comment :)",
                )

    def test__cancel_ticket_view__cancels_and_reactivates_tickets_as_expected(self):
        ticket_repeating = EventTicket.objects.create(user=self.user1, timeplace=self.repeating_time_place)
        ticket_standalone = EventTicket.objects.create(user=self.user1, event=self.standalone_event)

        for ticket in [ticket_repeating, ticket_standalone]:
            with self.subTest(ticket=ticket):
                ticket_detail_url = urlparse(reverse('ticket_detail', args=[ticket.pk])).path
                ticket_cancel_url = reverse('cancel_ticket', args=[ticket.pk])

                self.assertTrue(ticket.active)

                def assert_ticket_active_after_posting(active: bool):
                    response = self.client1.post(ticket_cancel_url)
                    self.assertRedirects(response, ticket_detail_url)

                    ticket.refresh_from_db()
                    self.assertEqual(ticket.active, active)

                assert_ticket_active_after_posting(False)
                # Posting to an already canceled ticket without the cancel permission, should do nothing
                assert_ticket_active_after_posting(False)
                self.user1.add_perms('news.cancel_ticket')
                assert_ticket_active_after_posting(True)
                assert_ticket_active_after_posting(False)
                self.user1.user_permissions.clear()

    def test__cancel_ticket_view__only_allows_expected_next_params(self):
        ticket_repeating = EventTicket.objects.create(user=self.user1, timeplace=self.repeating_time_place)
        ticket_standalone = EventTicket.objects.create(user=self.user1, event=self.standalone_event)

        for ticket in [ticket_repeating, ticket_standalone]:
            with self.subTest(ticket=ticket):
                ticket_detail_url = urlparse(reverse('ticket_detail', args=[ticket.pk])).path
                ticket_cancel_url = reverse('cancel_ticket', args=[ticket.pk])

                def assert_next_param_is_valid(next_param: str, valid: bool):
                    response = self.client1.post(f"{ticket_cancel_url}?next={next_param}")
                    expected_redirect_url = next_param if valid else ticket_detail_url
                    self.assertRedirects(response, expected_redirect_url, fetch_redirect_response=False)
                    ticket.active = True
                    ticket.save()

                # Check that it redirects to the detail URL when no `next` parameter is provided
                response = self.client1.post(ticket_cancel_url)
                self.assertRedirects(response, ticket_detail_url)
                ticket_repeating.active = True
                ticket_repeating.save()

                # Only `next` parameters that redirect the client to a URL on our website, are allowed
                assert_next_param_is_valid("google.com", False)
                assert_next_param_is_valid("/google.com", False)
                assert_next_param_is_valid("//google.com", False)
                assert_next_param_is_valid("http://google.com", False)
                assert_next_param_is_valid("https://google.com", False)
                assert_next_param_is_valid(f"google.com{ticket_detail_url}", False)
                assert_next_param_is_valid(ticket_detail_url, True)
                assert_next_param_is_valid(urlparse(reverse('my_tickets_list')).path, True)
                assert_next_param_is_valid(urlparse(reverse('event_detail', args=[ticket.registered_event.pk])).path, True)
                assert_next_param_is_valid("/", False)
                assert_next_param_is_valid(urlparse(reverse('front_page')).path, False)