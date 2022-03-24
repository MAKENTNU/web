from datetime import timedelta
from http import HTTPStatus
from typing import List, Tuple, Union

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from users.models import User
from util.test_utils import CleanUpTempFilesTestMixin, MOCK_JPG_FILE
from ...models import Event, EventTicket, TimePlace


class ViewTestCase(CleanUpTempFilesTestMixin, TestCase):

    def setUp(self):
        username = 'TEST_USER'
        password = 'TEST_PASS'
        self.user = User.objects.create_user(username=username, password=password)
        self.client.login(username=username, password=password)

        self.event = Event.objects.create(
            title='FUTURE',
            image=MOCK_JPG_FILE, image_description="Mock image",
            number_of_tickets=40,
        )
        self.timeplace = TimePlace.objects.create(
            event=self.event,
            start_time=timezone.localtime() + timedelta(minutes=5),
            end_time=timezone.localtime() + timedelta(minutes=10),
            number_of_tickets=29,
        )

    def test_events(self):
        response = self.client.get(reverse('event_list'))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_event(self):
        response = self.client.get(reverse('event_detail', args=[self.event.pk]))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_event_create(self):
        response = self.client.get(reverse('event_create'))
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

        self.user.add_perms('news.add_event')
        response = self.client.get(reverse('event_create'))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_event_edit(self):
        response = self.client.get(reverse('event_edit', args=[self.event.pk]))
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

        self.user.add_perms('news.change_event')
        response = self.client.get(reverse('event_edit', args=[self.event.pk]))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_timeplace_duplicate(self):
        time_place = TimePlace.objects.create(event=self.event, start_time=timezone.localtime() + timedelta(minutes=5),
                                              end_time=timezone.localtime() + timedelta(minutes=10))
        response = self.client.post(reverse('timeplace_duplicate', args=[self.event.pk, time_place.pk]))
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

        self.user.add_perms('news.add_timeplace', 'news.change_timeplace')
        response = self.client.post(reverse('timeplace_duplicate', args=[self.event.pk, time_place.pk]))

        duplicated_time_place = TimePlace.objects.exclude(pk=time_place.pk).latest('pk')
        self.assertRedirects(response, reverse('timeplace_edit', args=[self.event.pk, duplicated_time_place.pk]))

        new_start_time = time_place.start_time + timedelta(weeks=1)
        new_end_time = time_place.end_time + timedelta(weeks=1)
        self.assertTrue(duplicated_time_place.hidden)
        self.assertEqual(duplicated_time_place.start_time, new_start_time)
        self.assertEqual(duplicated_time_place.end_time, new_end_time)

    def test_timplace_duplicate_old(self):
        self.user.add_perms('news.add_timeplace', 'news.change_timeplace')

        start_time = timezone.localtime() - timedelta(weeks=2, days=3)
        end_time = start_time + timedelta(days=1)
        new_start_time = start_time + timedelta(weeks=3)
        new_end_time = end_time + timedelta(weeks=3)

        time_place = TimePlace.objects.create(event=self.event, start_time=start_time, end_time=end_time, hidden=False)
        response = self.client.post(reverse('timeplace_duplicate', args=[self.event.pk, time_place.pk]))
        duplicated_time_place = TimePlace.objects.exclude(pk=time_place.pk).latest('pk')

        self.assertRedirects(response, reverse('timeplace_edit', args=[self.event.pk, duplicated_time_place.pk]))
        self.assertEqual(duplicated_time_place.start_time, new_start_time)
        self.assertEqual(duplicated_time_place.end_time, new_end_time)

    def test_hidden_event(self):
        self.event.hidden = True
        self.event.save()

        response = self.client.get(reverse('event_detail', args=[self.event.pk]))
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

        self.user.add_perms('news.change_event')
        response = self.client.get(reverse('event_detail', args=[self.event.pk]))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_private_event(self):
        response = self.client.get(reverse('event_detail', args=[self.event.pk]))
        self.assertEqual(response.status_code, HTTPStatus.OK)

        self.event.private = True
        self.event.save()
        response = self.client.get(reverse('event_detail', args=[self.event.pk]))
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

        self.user.add_perms('news.can_view_private')
        response = self.client.get(reverse('event_detail', args=[self.event.pk]))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_event_context_ticket_emails_only_returns_active_tickets_emails(self):
        url_name = 'event_ticket_list'
        username_and_ticket_state_tuples = [
            ("user2", True),
            ("user3", False),
            ("user4", True),
        ]
        expected_context_ticket_emails = "user2@example.com,user4@example.com"

        self.assert_context_ticket_emails(url_name, self.event, username_and_ticket_state_tuples, expected_context_ticket_emails)

    def test_timeplace_context_ticket_emails_only_returns_active_tickets_emails(self):
        url_name = 'timeplace_ticket_list'
        username_and_ticket_state_tuples = [
            ("user2", True),
            ("user3", False),
            ("user4", True),
        ]
        expected_context_ticket_emails = "user2@example.com,user4@example.com"

        self.assert_context_ticket_emails(url_name, self.timeplace, username_and_ticket_state_tuples, expected_context_ticket_emails)

    def test_event_context_ticket_emails_returns_tickets_email_after_reregistration(self):
        url_name = 'event_ticket_list'
        username_and_ticket_state_tuples = [
            ("user2", False),
            ("user2", True),
        ]
        expected_context_ticket_emails = "user2@example.com"

        self.assert_context_ticket_emails(url_name, self.event, username_and_ticket_state_tuples, expected_context_ticket_emails)

    def test_timeplace_context_ticket_emails_returns_tickets_email_after_reregistration(self):
        url_name = 'timeplace_ticket_list'
        username_and_ticket_state_tuples = [
            ("user2", False),
            ("user2", True),
        ]
        expected_context_ticket_emails = "user2@example.com"

        self.assert_context_ticket_emails(url_name, self.timeplace, username_and_ticket_state_tuples, expected_context_ticket_emails)

    def assert_context_ticket_emails(self, url_name: str, event: Union[Event, TimePlace],
                                     username_and_ticket_state_tuples: List[Tuple[str, bool]], expected_context_ticket_emails: str):
        """
        Asserts that the ``ticket_emails`` in context at ``url_name`` equals ``expected_context_ticket_emails``.

        :param url_name: Name of URL path
        :param event: Event or TimePlace that the tickets belong to
        :param username_and_ticket_state_tuples: List of tuples in the format ``(username: str, ticket_state: boolean)``
        :param expected_context_ticket_emails: The expected string of comma separated ticket emails

        :return: Boolean based on whether ``context['ticket_emails'] == expected_context_ticket_emails`` and status code is 200
        """

        self.create_tickets_for(event, username_and_ticket_state_tuples)
        self.user.add_perms('news.change_event')

        url_args = [event.event.pk, event.pk] if isinstance(event, TimePlace) else [event.pk]
        response = self.client.get(reverse(url_name, args=url_args))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(expected_context_ticket_emails, response.context["ticket_emails"])

    @staticmethod
    def create_tickets_for(event: Union[Event, TimePlace], username_and_ticket_state_tuples: List[Tuple[str, bool]]):
        """
        Creates a list of active and inactive tickets for the provided ``event`` from ``username_and_ticket_state_tuples``.

        :param event: Event or TimePlace model that the ticket belongs to
        :param username_and_ticket_state_tuples: List of tuples in the format ``(username: str, ticket_state: boolean)``

        :return: List of tickets to ``event`` with the details from ``username_and_ticket_state_tuples``
        """

        event_arg_name = 'timeplace' if isinstance(event, TimePlace) else 'event'
        tickets = []
        for username, ticket_state in username_and_ticket_state_tuples:
            user = User.objects.get_or_create(username=username, email=f"{username}@example.com")[0]
            ticket, _created = EventTicket.objects.get_or_create(
                user=user,
                **{event_arg_name: event},
            )
            ticket.active = ticket_state
            ticket.save()
            tickets.append(ticket)
        return tickets
