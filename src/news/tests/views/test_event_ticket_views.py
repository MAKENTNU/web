import io
from contextlib import redirect_stdout
from datetime import timedelta
from http import HTTPStatus
from urllib.parse import urlparse

from django.conf import settings
from django.test import Client, TestCase
from django.urls import reverse as django_reverse
from django.utils import lorem_ipsum, timezone
from django_hosts import reverse

from users.models import User
from util.model_utils import duplicate
from util.test_utils import CleanUpTempFilesTestMixin, MOCK_JPG_FILE
from web.multilingual.data_structures import MultiLingualTextStructure
from ...models import Event, EventTicket, TimePlace


class TestEventTicketViews(CleanUpTempFilesTestMixin, TestCase):

    def setUp(self):
        now = timezone.localtime()

        self.repeating_event = Event.objects.create(title=MultiLingualTextStructure("Repeating event"), image=MOCK_JPG_FILE,
                                                    event_type=Event.Type.REPEATING)
        self.repeating_time_place = TimePlace.objects.create(
            event=self.repeating_event, start_time=now, end_time=now + timedelta(hours=1), hidden=False,
            number_of_tickets=10,
        )

        self.standalone_event = Event.objects.create(title=MultiLingualTextStructure("Standalone event"), image=MOCK_JPG_FILE,
                                                     event_type=Event.Type.STANDALONE, number_of_tickets=10)
        self.standalone_time_place = TimePlace.objects.create(
            event=self.standalone_event, start_time=now, end_time=now + timedelta(hours=1), hidden=False,
        )

        self.user1 = User.objects.create_user(username="user1", email="dev@makentnu.no")
        self.client1 = Client()
        self.client1.force_login(self.user1)

    def test__event_registration_view__can_only_be_viewed_with_correct_url_for_event_type(self):
        def assert_response_status_code(url: str, status_code: int):
            response = self.client1.get(url)
            self.assertEqual(response.status_code, status_code)

        assert_response_status_code(reverse('event_ticket_create', args=[self.repeating_event.pk]), HTTPStatus.FORBIDDEN)
        assert_response_status_code(reverse('event_ticket_create', args=[self.repeating_event.pk, self.repeating_time_place.pk]), HTTPStatus.OK)
        assert_response_status_code(reverse('event_ticket_create', args=[self.standalone_event.pk]), HTTPStatus.OK)
        assert_response_status_code(reverse('event_ticket_create', args=[self.standalone_event.pk, self.standalone_time_place.pk]),
                                    HTTPStatus.FORBIDDEN)

    def test__event_registration_view__can_only_be_viewed_with_correct_combination_of_event_and_time_place(self):
        repeating_event1 = self.repeating_event
        repeating_event2 = duplicate(self.repeating_event)
        repeating_time_place1 = self.repeating_time_place
        repeating_time_place2 = duplicate(self.repeating_time_place, event=repeating_event2)

        def assert_response_status_code(url_args: list, status_code: int):
            url = reverse('event_ticket_create', args=url_args)
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

    def test__event_registration_view__sends_emails(self):
        registration_urls = (
            reverse('event_ticket_create', args=[self.repeating_event.pk, self.repeating_time_place.pk]),
            reverse('event_ticket_create', args=[self.standalone_event.pk]),
        )
        ticket_data = (
            {'language': language, 'comment': comment}
            for language in EventTicket.Language.values
            for comment in (
                "",
                "A comment :)",
                "Æøå",
                self.get_max_length_ticket_comment(),
            )
        )
        for url in registration_urls:
            for data in ticket_data:
                with self.subTest(url=url, data=data):
                    self.assertEqual(self.user1.event_tickets.count(), 0)

                    # Create a ticket by registering for the event, while capturing whatever is printed to the console
                    console_output = io.StringIO()
                    with redirect_stdout(console_output):
                        response = self.client1.post(url, data)
                    self.assertEqual(response.status_code, HTTPStatus.FOUND)

                    # Get the created ticket
                    self.assertEqual(self.user1.event_tickets.count(), 1)
                    ticket: EventTicket = self.user1.event_tickets.get()

                    # Check that the email was indeed printed to the console
                    printed_email_str = console_output.getvalue()
                    self.assertIn(f"From: {settings.EVENT_TICKET_EMAIL}", printed_email_str)
                    self.assertIn(f"To: {self.user1.email}", printed_email_str)
                    self.assertIn("Content-Type: text/plain", printed_email_str)
                    self.assertIn("Content-Type: text/html", printed_email_str)

                    def count_fail_message(search_str):
                        return f'The following string did not contain the expected number of occurrences of "{search_str}":\n{printed_email_str}'

                    self.assertEqual(printed_email_str.count(str(ticket.registered_event.title)), 2,
                                     count_fail_message(ticket.registered_event.title))
                    self.assertEqual(printed_email_str.count(str(ticket.uuid)), 6,
                                     count_fail_message(ticket.uuid))

                    # Delete the ticket, so that the next for-loop iteration has a clean slate
                    ticket.delete()

    @staticmethod
    def get_max_length_ticket_comment():
        comment_max_length = EventTicket._meta.get_field('comment').max_length
        max_length_comment = lorem_ipsum.sentence()
        while len(max_length_comment) < comment_max_length:
            max_length_comment = f"{max_length_comment}\n{lorem_ipsum.sentence()}"
        # Make each line shorter by placing a newline after every comma instead of a space
        return max_length_comment.replace(", ", ",\n")[:comment_max_length]

    def test__event_registration_view__creates_and_reactivates_tickets_as_expected(self):
        for time_place_or_event in [self.repeating_time_place, self.standalone_event]:
            with self.subTest(time_place_or_event=time_place_or_event):
                if isinstance(time_place_or_event, TimePlace):
                    registration_url = reverse('event_ticket_create', args=[time_place_or_event.event.pk, time_place_or_event.pk])
                else:
                    registration_url = reverse('event_ticket_create', args=[time_place_or_event.pk])

                self.assertEqual(time_place_or_event.tickets.count(), 0)

                def assert_results_after_registering_for_event(posted_data: dict, *, expected_form_instance: EventTicket | None,
                                                               expected_language: str, expected_comment: str) -> EventTicket:
                    form_instance = self.client1.get(registration_url).context['form'].instance
                    if expected_form_instance:
                        self.assertEqual(form_instance, expected_form_instance)
                    else:
                        self.assertFalse(EventTicket.objects.filter(pk=form_instance.pk).exists())

                    response = self.client1.post(registration_url, posted_data)

                    self.assertEqual(time_place_or_event.tickets.count(), 1)
                    ticket = time_place_or_event.tickets.get()

                    ticket_detail_url = reverse('event_ticket_detail', args=[ticket.pk])
                    self.assertRedirects(response, ticket_detail_url)

                    self.assertEqual(ticket.language, expected_language)
                    self.assertEqual(ticket.comment, expected_comment)
                    self.assertTrue(ticket.active)
                    return ticket

                created_ticket = assert_results_after_registering_for_event(
                    {'language': 'nb'},
                    expected_form_instance=None, expected_language='nb', expected_comment="",
                )
                self.assertEqual(created_ticket.active_last_modified, created_ticket.creation_date)

                created_ticket.active = False
                created_ticket.save()

                reactivated_ticket = assert_results_after_registering_for_event(
                    {'language': 'en', 'comment': "A comment :)"},
                    expected_form_instance=created_ticket, expected_language='en', expected_comment="A comment :)",
                )
                self.assertEqual(reactivated_ticket.creation_date, created_ticket.creation_date)
                self.assertGreater(reactivated_ticket.active_last_modified, reactivated_ticket.creation_date)

    def test__event_ticket_cancel_view__cancels_and_reactivates_tickets_as_expected(self):
        ticket_repeating = EventTicket.objects.create(user=self.user1, timeplace=self.repeating_time_place)
        ticket_standalone = EventTicket.objects.create(user=self.user1, event=self.standalone_event)

        for ticket in [ticket_repeating, ticket_standalone]:
            with self.subTest(ticket=ticket):
                ticket_detail_url = reverse('event_ticket_detail', args=[ticket.pk])
                ticket_cancel_url = reverse('event_ticket_cancel', args=[ticket.pk])

                self.assertTrue(ticket.active)
                self.assertEqual(ticket.active_last_modified, ticket.creation_date)

                def assert_ticket_active_after_posting(active: bool):
                    response = self.client1.post(ticket_cancel_url)
                    self.assertRedirects(response, ticket_detail_url)

                    ticket.refresh_from_db()
                    self.assertEqual(ticket.active, active)

                assert_ticket_active_after_posting(False)
                last_modified = ticket.active_last_modified
                self.assertGreater(last_modified, ticket.creation_date)
                # Posting to an already canceled ticket without the cancel permission, should do nothing
                assert_ticket_active_after_posting(False)
                self.assertEqual(ticket.active_last_modified, last_modified)

                self.user1.add_perms('news.cancel_ticket')
                assert_ticket_active_after_posting(True)
                assert_ticket_active_after_posting(False)
                self.assertGreater(ticket.active_last_modified, last_modified)

                self.user1.user_permissions.clear()

    # noinspection HttpUrlsUsage
    def test__event_ticket_cancel_view__only_allows_expected_next_params(self):
        ticket_repeating = EventTicket.objects.create(user=self.user1, timeplace=self.repeating_time_place)
        ticket_standalone = EventTicket.objects.create(user=self.user1, event=self.standalone_event)

        for ticket in [ticket_repeating, ticket_standalone]:
            with self.subTest(ticket=ticket):
                ticket_detail_url = reverse('event_ticket_detail', args=[ticket.pk])
                ticket_cancel_url = reverse('event_ticket_cancel', args=[ticket.pk])

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

                # Various external URLs, which should not be allowed
                assert_next_param_is_valid("google.com", False)
                assert_next_param_is_valid("/google.com", False)
                assert_next_param_is_valid("//google.com", False)
                assert_next_param_is_valid("http://google.com", False)
                assert_next_param_is_valid("https://google.com", False)
                assert_next_param_is_valid(f"google.com{ticket_detail_url}", False)
                # The URLs listed in `EventTicketCancelView.get_allowed_next_params()`, which should be allowed
                assert_next_param_is_valid(ticket_detail_url, True)
                self.assertEqual(ticket.get_absolute_url(), ticket_detail_url)
                assert_next_param_is_valid(django_reverse('event_ticket_detail', args=[ticket.pk]), True)
                assert_next_param_is_valid(reverse('event_ticket_my_list'), True)
                assert_next_param_is_valid(django_reverse('event_ticket_my_list'), True)
                assert_next_param_is_valid(reverse('event_detail', args=[ticket.registered_event.pk]), True)
                assert_next_param_is_valid(django_reverse('event_detail', args=[ticket.registered_event.pk]), True)
                # Some other internal URLs, which should not be allowed
                assert_next_param_is_valid("/", False)
                assert_next_param_is_valid(urlparse(reverse('front_page')).path, False)
