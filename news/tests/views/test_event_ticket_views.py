from datetime import timedelta
from urllib.parse import urlparse

from django.test import Client, TestCase
from django.utils import timezone
from django_hosts import reverse

from users.models import User
from ...models import Event, EventTicket, TimePlace


class TestEventTicketViews(TestCase):

    def setUp(self):
        now = timezone.localtime()

        self.repeating_event = Event.objects.create(title="Repeating event", event_type=Event.Type.REPEATING)
        self.repeating_time_place = TimePlace.objects.create(
            event=self.repeating_event, start_time=now, end_time=now + timedelta(hours=1),
            number_of_tickets=10,
        )

        self.standalone_event = Event.objects.create(title="Standalone event", event_type=Event.Type.STANDALONE, number_of_tickets=10)
        self.standalone_time_place = TimePlace.objects.create(
            event=self.standalone_event, start_time=now, end_time=now + timedelta(hours=1),
        )

        self.user1 = User.objects.create_user(username="user1")
        self.client1 = Client()
        self.client1.force_login(self.user1)

    def test__cancel_ticket_view__only_allows_expected_next_params(self):
        ticket_repeating = EventTicket.objects.create(user=self.user1, timeplace=self.repeating_time_place)
        ticket_standalone = EventTicket.objects.create(user=self.user1, event=self.standalone_event)

        for ticket in [ticket_repeating, ticket_standalone]:
            ticket_detail_url = urlparse(reverse('ticket_detail', args=[ticket.pk])).path
            ticket_cancel_url = reverse('cancel_ticket', args=[ticket.pk])
            with self.subTest(ticket_cancel_url=ticket_cancel_url):

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
                assert_next_param_is_valid("/google.com", True)
                assert_next_param_is_valid("//google.com", False)
                assert_next_param_is_valid("http://google.com", False)
                assert_next_param_is_valid("https://google.com", False)
                assert_next_param_is_valid(f"google.com{ticket_detail_url}", False)
                assert_next_param_is_valid(ticket_detail_url, True)
                assert_next_param_is_valid(urlparse(reverse('my_tickets_list')).path, True)
                assert_next_param_is_valid(urlparse(reverse('event_detail', args=[ticket.event or ticket.timeplace.event])).path, True)
                assert_next_param_is_valid("/", True)
                assert_next_param_is_valid(urlparse(reverse('front_page')).path, True)
