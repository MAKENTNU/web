import json
from datetime import timedelta

from django.contrib.auth.models import Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from users.models import User
from .models import Article, Event, TimePlace, EventTicket

# A very small JPEG image without any content. Used for creation of simple images when creating an article
simple_jpg = b'\xff\xd8\xff\xdb\x00C\x00\x03\x02\x02\x02\x02\x02\x03\x02\x02\x02\x03\x03\x03\x03\x04\x06\x04\x04\x04' \
             b'\x04\x04\x08\x06\x06\x05\x06\t\x08\n\n\t\x08\t\t\n\x0c\x0f\x0c\n\x0b\x0e\x0b\t\t\r\x11\r\x0e\x0f\x10' \
             b'\x10\x11\x10\n\x0c\x12\x13\x12\x10\x13\x0f\x10\x10\x10\xff\xc9\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11' \
             b'\x00\xff\xcc\x00\x06\x00\x10\x10\x05\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xd2\xcf \xff\xd9'


class ModelTestCase(TestCase):

    @staticmethod
    def create_time_place(event, publication_time_adjust_days, start_time_adjust_seconds,
                          hidden=TimePlace._meta.get_field("hidden").default):
        return TimePlace.objects.create(
            event=event,
            publication_time=timezone.localtime() + timedelta(days=publication_time_adjust_days),
            start_time=timezone.localtime() + timedelta(seconds=start_time_adjust_seconds),
            end_time=timezone.localtime() + timedelta(minutes=1, seconds=start_time_adjust_seconds),
            hidden=hidden,
        )

    def test_str(self):
        article = Article.objects.create(title='TEST_TITLE')
        self.assertEqual(article.title, 'TEST_TITLE')
        self.assertEqual(article.title, str(article))

        title = 'Test event'
        event = Event.objects.create(title=title)
        time_place = self.create_time_place(event, 0, 0)
        date_str = timezone.now().date().strftime('%Y.%m.%d')
        self.assertEqual(str(time_place), f"{title} - {date_str}")

    def test_article_manager(self):
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
        self.assertEqual(set(Article.objects.published()), {published1, published2})

    def test_event_manager(self):
        event = Event.objects.create(title='', hidden=False)
        hidden_event = Event.objects.create(title='', hidden=True)

        not_published = self.create_time_place(event, 1, 1, False)
        future = self.create_time_place(event, -1, 1, False)
        past = self.create_time_place(event, -1, -100, False)

        self.create_time_place(hidden_event, -1, 1)
        self.create_time_place(hidden_event, -1, -1)
        self.create_time_place(hidden_event, -1, 1, False)
        self.create_time_place(hidden_event, -1, -1, False)

        self.assertEqual(TimePlace.objects.future().count(), 1)
        self.assertEqual(TimePlace.objects.past().count(), 1)
        self.assertEqual(TimePlace.objects.future().first(), future)
        self.assertEqual(TimePlace.objects.past().first(), past)


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
            image=SimpleUploadedFile(name='img.jpg', content=simple_jpg, content_type='image/jpeg'),
            publication_time=timezone.localtime() - timedelta(days=1),
        )
        self.event = Event.objects.create(
            title='FUTURE',
            image=SimpleUploadedFile(name='img.jpg', content=simple_jpg, content_type='image/jpeg'),
            number_of_tickets=40,
        )
        self.timeplace = TimePlace.objects.create(
            event=self.event,
            start_time=timezone.localtime() + timedelta(minutes=5),
            end_time=timezone.localtime() + timedelta(minutes=10),
            number_of_tickets=29
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
        event = self.event
        username_and_ticket_state_tuples = [
            ("user2", True),
            ("user3", False),
            ("user4", True),
        ]
        expected_context_ticket_emails = "user2@example.com,user4@example.com"

        self.assert_context_ticket_emails(
            url_name=url_name,
            event=event,
            username_and_ticket_state_tuples=username_and_ticket_state_tuples,
            expected_context_ticket_emails=expected_context_ticket_emails
        )

    def test_timeplace_context_ticket_emails_only_returns_active_tickets_emails(self):
        url_name = "timeplace-tickets"
        event = self.timeplace
        username_and_ticket_state_tuples = [
            ("user2", True),
            ("user3", False),
            ("user4", True),
        ]
        expected_context_ticket_emails = "user2@example.com,user4@example.com"

        self.assert_context_ticket_emails(
            url_name=url_name,
            event=event,
            username_and_ticket_state_tuples=username_and_ticket_state_tuples,
            expected_context_ticket_emails=expected_context_ticket_emails
        )

    def test_event_context_ticket_emails_returns_tickets_email_after_reregistration(self):
        url_name = "event-tickets"
        event = self.event
        username_and_ticket_state_tuples = [
            ("user2", True),
            ("user2", False),
        ]
        expected_context_ticket_emails = "user2@example.com"

        self.assert_context_ticket_emails(
            url_name=url_name,
            event=event,
            username_and_ticket_state_tuples=username_and_ticket_state_tuples,
            expected_context_ticket_emails=expected_context_ticket_emails
        )

    def test_timeplace_context_ticket_emails_returns_tickets_email_after_reregistration(self):
        url_name = "timeplace-tickets"
        event = self.timeplace
        username_and_ticket_state_tuples = [
            ("user2", True),
            ("user2", False),
        ]
        expected_context_ticket_emails = "user2@example.com"

        self.assert_context_ticket_emails(
            url_name=url_name,
            event=event,
            username_and_ticket_state_tuples=username_and_ticket_state_tuples,
            expected_context_ticket_emails=expected_context_ticket_emails
        )

    def assert_context_ticket_emails(self, url_name, event, username_and_ticket_state_tuples, expected_context_ticket_emails):
        """
        Asserts that the `ticket_emails` in context at ``url_name`` equals ``expected_context_ticket_emails``

        :param url_name: Name of URL
        :param event: Event or TimePlace that the tickets belong to
        :param username_and_ticket_state_tuples: List of tuples on the format `(username: str, ticket_state: boolean)`
        :param expected_context_ticket_emails: The expected string of comma separated ticket emails

        :return: Boolean based on `context['ticket_emails']` is `expected_context_ticket_emails` and status code is 200
        """

        tickets = self.create_tickets_for(
            event=event,
            username_and_ticket_state_tuples=username_and_ticket_state_tuples
        )
        self.add_permission("change_event")

        response = self.client.get(reverse(url_name, args=[event.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(expected_context_ticket_emails, response.context["ticket_emails"])

    @staticmethod
    def create_tickets_for(event, username_and_ticket_state_tuples):
        """
        Creates a list of active and inactive tickets for the provided ``event`` from ``username_and_ticket_state_tuples``.

        :param event: Event or TimePlace model that the ticket belongs to
        :param username_and_ticket_state_tuples: List of tuples on the format `(username: str, ticket_state: boolean)`

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
            image=SimpleUploadedFile(name='img.jpg', content=simple_jpg, content_type='image/jpeg'),
            publication_time=timezone.now() - timedelta(days=1),
            hidden=True,
            private=False,
        )
        self.event = Event.objects.create(
            title='',
            image=SimpleUploadedFile(name='img.jpg', content=simple_jpg, content_type='image/jpeg'),
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
