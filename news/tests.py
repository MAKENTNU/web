import json
from datetime import timedelta

from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from users.models import User
from util.test_utils import MOCK_JPG_FILE
from .models import Article, Event, EventTicket, TimePlace


class ModelTestCase(TestCase):

    @staticmethod
    def create_time_place(event, *, publication_time_adjust_days, start_time_adjust_seconds,
                          hidden=TimePlace._meta.get_field("hidden").default):
        now = timezone.localtime()
        start_time = now + timedelta(seconds=start_time_adjust_seconds)
        return TimePlace.objects.create(
            event=event,
            publication_time=now + timedelta(days=publication_time_adjust_days),
            start_time=start_time,
            end_time=start_time + timedelta(minutes=1),
            hidden=hidden,
        )

    def test_str(self):
        article = Article.objects.create(title='TEST_TITLE')
        self.assertEqual(article.title, 'TEST_TITLE')
        self.assertEqual(article.title, str(article))

        title = 'Test event'
        event = Event.objects.create(title=title)
        time_place = self.create_time_place(event, publication_time_adjust_days=0, start_time_adjust_seconds=0)
        date_str = timezone.localdate().strftime("%d.%m.%Y")
        self.assertEqual(str(time_place), f"{title} - {date_str}")

    def test_article_queryset(self):
        Article.objects.create(
            title='NOT PUBLISHED',
            publication_time=timezone.localtime() + timedelta(days=1),
        )
        Article.objects.create(
            title='NOT PUBLISHED',
            publication_time=timezone.localtime() + timedelta(seconds=1),
        )
        published1 = Article.objects.create(
            title='PUBLISHED',
            publication_time=timezone.localtime() - timedelta(days=1),
        )
        published2 = Article.objects.create(
            title='PUBLISHED',
            publication_time=timezone.localtime() - timedelta(seconds=1),
        )
        self.assertEqual(Article.objects.published().count(), 2)
        self.assertSetEqual(set(Article.objects.published()), {published1, published2})

    def test_timeplace_queryset(self):
        event = Event.objects.create(title='', hidden=False)
        hidden_event = Event.objects.create(title='', hidden=True)

        event_not_published = self.create_time_place(event, publication_time_adjust_days=1, start_time_adjust_seconds=1, hidden=False)
        event_future = self.create_time_place(event, publication_time_adjust_days=-1, start_time_adjust_seconds=1, hidden=False)
        event_past = self.create_time_place(event, publication_time_adjust_days=-1, start_time_adjust_seconds=-100, hidden=False)

        self.create_time_place(hidden_event, publication_time_adjust_days=-1, start_time_adjust_seconds=1)
        self.create_time_place(hidden_event, publication_time_adjust_days=-1, start_time_adjust_seconds=-1)
        self.create_time_place(hidden_event, publication_time_adjust_days=-1, start_time_adjust_seconds=1, hidden=False)
        self.create_time_place(hidden_event, publication_time_adjust_days=-1, start_time_adjust_seconds=-1, hidden=False)

        self.assertEqual(TimePlace.objects.future().count(), 1)
        self.assertEqual(TimePlace.objects.past().count(), 1)
        self.assertEqual(TimePlace.objects.future().first(), event_future)
        self.assertEqual(TimePlace.objects.past().first(), event_past)


class ViewTestCase(TestCase):

    def add_permission(self, codename):
        permission = Permission.objects.get(codename=codename)
        self.user.user_permissions.add(permission)

    def setUp(self):
        username = 'TEST_USER'
        password = 'TEST_PASS'
        self.user = User.objects.create_user(username=username, password=password)
        self.client.login(username=username, password=password)

        self.article = Article.objects.create(
            title='PUBLISHED',
            image=MOCK_JPG_FILE,
            publication_time=timezone.localtime() - timedelta(days=1),
        )
        self.event = Event.objects.create(
            title='FUTURE',
            image=MOCK_JPG_FILE,
            number_of_tickets=40,
        )
        self.timeplace = TimePlace.objects.create(
            event=self.event,
            start_time=timezone.localtime() + timedelta(minutes=5),
            end_time=timezone.localtime() + timedelta(minutes=10),
            number_of_tickets=29,
        )

    def test_admin(self):
        response = self.client.get(reverse('admin-articles'))
        self.assertNotEqual(response.status_code, 200)

        self.add_permission('change_article')
        response = self.client.get(reverse('admin-articles'))
        self.assertEqual(response.status_code, 200)

    def test_articles(self):
        response = self.client.get(reverse('articles'))
        self.assertEqual(response.status_code, 200)

    def test_article(self):
        response = self.client.get(reverse('article', kwargs={'pk': self.article.pk}))
        self.assertEqual(response.status_code, 200)

    def test_article_create(self):
        response = self.client.get(reverse('article-create'))
        self.assertNotEqual(response.status_code, 200)

        self.add_permission('add_article')
        response = self.client.get(reverse('article-create'))
        self.assertEqual(response.status_code, 200)

    def test_article_edit(self):
        response = self.client.get(reverse('article-edit', kwargs={'pk': self.article.pk}))
        self.assertNotEqual(response.status_code, 200)

        self.add_permission('change_article')
        response = self.client.get(reverse('article-edit', kwargs={'pk': self.article.pk}))
        self.assertEqual(response.status_code, 200)

    def test_events(self):
        response = self.client.get(reverse('events'))
        self.assertEqual(response.status_code, 200)

    def test_event(self):
        response = self.client.get(reverse('event', kwargs={'pk': self.event.pk}))
        self.assertEqual(response.status_code, 200)

    def test_event_create(self):
        response = self.client.get(reverse('event-create'))
        self.assertNotEqual(response.status_code, 200)

        self.add_permission('add_event')
        response = self.client.get(reverse('event-create'))
        self.assertEqual(response.status_code, 200)

    def test_event_edit(self):
        response = self.client.get(reverse('event-edit', kwargs={'pk': self.event.pk}))
        self.assertNotEqual(response.status_code, 200)

        self.add_permission('change_event')
        response = self.client.get(reverse('event-edit', kwargs={'pk': self.event.pk}))
        self.assertEqual(response.status_code, 200)

    def test_timeplace_duplicate(self):
        tp = TimePlace.objects.create(event=self.event, start_time=timezone.localtime() + timedelta(minutes=5),
                                      end_time=timezone.localtime() + timedelta(minutes=10))
        response = self.client.get(reverse('timeplace-duplicate', args=[tp.pk]))
        self.assertNotEqual(response.status_code, 200)

        self.add_permission('add_timeplace')
        self.add_permission('change_timeplace')
        response = self.client.get(reverse('timeplace-duplicate', args=[tp.pk]))

        new = TimePlace.objects.exclude(pk=tp.pk).latest('pk')
        self.assertRedirects(response, reverse('timeplace-edit', args=[new.pk]))

        new_start_time = tp.start_time + timedelta(weeks=1)
        new_end_time = tp.end_time + timedelta(weeks=1)
        self.assertTrue(new.hidden)
        self.assertEqual(new.start_time, new_start_time)
        self.assertEqual(new.end_time, new_end_time)

    def test_timplace_duplicate_old(self):
        self.add_permission('add_timeplace')
        self.add_permission('change_timeplace')

        start_time = timezone.localtime() - timedelta(weeks=2, days=3)
        end_time = start_time + timedelta(days=1)
        new_start_time = start_time + timedelta(weeks=3)
        new_end_time = end_time + timedelta(weeks=3)

        tp = TimePlace.objects.create(
            event=self.event,
            start_time=start_time,
            end_time=end_time,
            hidden=False,
        )

        response = self.client.get(reverse('timeplace-duplicate', args=[tp.pk]))
        self.assertNotEqual(response.status_code, 200)
        new = TimePlace.objects.exclude(pk=tp.pk).latest('pk')

        self.assertEqual(new.start_time, new_start_time)
        self.assertEqual(new.end_time, new_end_time)

    def test_admin_article_toggle_view(self):
        def toggle(pk, attr):
            response = self.client.post(reverse('article-toggle'), {'pk': pk, 'toggle': attr})
            self.assertEqual(response.status_code, 200)
            return json.loads(response.content)

        self.add_permission('change_article')
        self.assertEquals(toggle(-1, 'hidden'), {})
        self.assertEquals(toggle(self.article.pk, 'ajfal'), {})

        hidden = self.article.hidden
        self.assertEquals(toggle(self.article.pk, 'hidden'), {'color': 'grey' if hidden else 'yellow'})
        self.assertEquals(toggle(self.article.pk, 'hidden'), {'color': 'yellow' if hidden else 'grey'})

    def test_event_context_ticket_emails_only_returns_active_tickets_emails(self):
        url_name = "event-tickets"
        username_and_ticket_state_tuples = [
            ("user2", True),
            ("user3", False),
            ("user4", True),
        ]
        expected_context_ticket_emails = "user2@example.com,user4@example.com"

        self.assert_context_ticket_emails(url_name, self.event, username_and_ticket_state_tuples, expected_context_ticket_emails)

    def test_timeplace_context_ticket_emails_only_returns_active_tickets_emails(self):
        url_name = "timeplace-tickets"
        username_and_ticket_state_tuples = [
            ("user2", True),
            ("user3", False),
            ("user4", True),
        ]
        expected_context_ticket_emails = "user2@example.com,user4@example.com"

        self.assert_context_ticket_emails(url_name, self.timeplace, username_and_ticket_state_tuples, expected_context_ticket_emails)

    def test_event_context_ticket_emails_returns_tickets_email_after_reregistration(self):
        url_name = "event-tickets"
        username_and_ticket_state_tuples = [
            ("user2", True),
            ("user2", False),
        ]
        expected_context_ticket_emails = "user2@example.com"

        self.assert_context_ticket_emails(url_name, self.event, username_and_ticket_state_tuples, expected_context_ticket_emails)

    def test_timeplace_context_ticket_emails_returns_tickets_email_after_reregistration(self):
        url_name = "timeplace-tickets"
        username_and_ticket_state_tuples = [
            ("user2", True),
            ("user2", False),
        ]
        expected_context_ticket_emails = "user2@example.com"

        self.assert_context_ticket_emails(url_name, self.timeplace, username_and_ticket_state_tuples, expected_context_ticket_emails)

    def assert_context_ticket_emails(self, url_name, event, username_and_ticket_state_tuples, expected_context_ticket_emails):
        """
        Asserts that the ``ticket_emails`` in context at ``url_name`` equals ``expected_context_ticket_emails``.

        :param url_name: Name of URL path
        :param event: Event or TimePlace that the tickets belong to
        :param username_and_ticket_state_tuples: List of tuples in the format ``(username: str, ticket_state: boolean)``
        :param expected_context_ticket_emails: The expected string of comma separated ticket emails

        :return: Boolean based on whether ``context['ticket_emails'] == expected_context_ticket_emails`` and status code is 200
        """

        self.create_tickets_for(event, username_and_ticket_state_tuples)
        self.add_permission("change_event")

        response = self.client.get(reverse(url_name, args=[event.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(expected_context_ticket_emails, response.context["ticket_emails"])

    @staticmethod
    def create_tickets_for(event, username_and_ticket_state_tuples):
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
            tickets.append(
                EventTicket.objects.create(
                    user=user,
                    active=ticket_state,
                    **{event_arg_name: event},
                )
            )
        return tickets


class HiddenPrivateTestCase(TestCase):

    def add_permission(self, codename):
        permission = Permission.objects.get(codename=codename)
        self.user.user_permissions.add(permission)

    def setUp(self):
        username = 'TEST_USER'
        password = 'TEST_PASS'
        self.user = User.objects.create_user(username=username, password=password)
        self.client.login(username=username, password=password)

        self.article = Article.objects.create(
            title='',
            image=MOCK_JPG_FILE,
            publication_time=timezone.now() - timedelta(days=1),
            hidden=True,
            private=False,
        )
        self.event = Event.objects.create(
            title='',
            image=MOCK_JPG_FILE,
            hidden=True,
            private=False,
        )

    def test_hidden_event(self):
        response = self.client.get(reverse('event', kwargs={'pk': self.event.pk}))
        self.assertEqual(response.status_code, 404)

        self.add_permission('change_event')
        response = self.client.get(reverse('event', kwargs={'pk': self.event.pk}))
        self.assertEqual(response.status_code, 200)

    def test_hidden_article(self):
        response = self.client.get(reverse('article', kwargs={'pk': self.article.pk}))
        self.assertEqual(response.status_code, 404)

        self.add_permission('change_article')
        response = self.client.get(reverse('article', kwargs={'pk': self.article.pk}))
        self.assertEqual(response.status_code, 200)

    def test_private_event(self):
        self.event.hidden = False
        self.event.save()
        response = self.client.get(reverse('event', kwargs={'pk': self.event.pk}))
        self.assertEqual(response.status_code, 200)

        self.event.private = True
        self.event.save()
        response = self.client.get(reverse('event', kwargs={'pk': self.event.pk}))
        self.assertEqual(response.status_code, 404)

        self.add_permission('can_view_private')
        response = self.client.get(reverse('event', kwargs={'pk': self.event.pk}))
        self.assertEqual(response.status_code, 200)

    def test_private_article(self):
        self.article.hidden = False
        self.article.save()
        response = self.client.get(reverse('article', kwargs={'pk': self.article.pk}))
        self.assertEqual(response.status_code, 200)

        self.article.private = True
        self.article.save()
        response = self.client.get(reverse('article', kwargs={'pk': self.article.pk}))
        self.assertEqual(response.status_code, 404)

        self.add_permission('can_view_private')
        response = self.client.get(reverse('article', kwargs={'pk': self.article.pk}))
        self.assertEqual(response.status_code, 200)

    def test_not_published_article(self):
        self.article.hidden = False

        self.article.publication_time = timezone.now() - timedelta(days=1)
        self.article.save()
        response = self.client.get(reverse('article', kwargs={'pk': self.article.pk}))
        self.assertEqual(response.status_code, 200)

        self.article.publication_time = timezone.now() + timedelta(days=1)
        self.article.save()
        response = self.client.get(reverse('article', kwargs={'pk': self.article.pk}))
        self.assertEqual(response.status_code, 404)

        self.add_permission('change_article')
        response = self.client.get(reverse('article', kwargs={'pk': self.article.pk}))
        self.assertEqual(response.status_code, 200)
