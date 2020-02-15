import json
from datetime import timedelta

from users.models import User
from django.contrib.auth.models import Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from news.models import Article, Event, TimePlace


class ModelTestCase(TestCase):

    @staticmethod
    def create_time_place(event, pub_date_adjust_days, start_time_adjust_seconds,
                          hidden=TimePlace._meta.get_field("hidden").default):
        return TimePlace.objects.create(
            event=event,
            publication_time=timezone.localtime() + timedelta(days=pub_date_adjust_days),
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
        past = self.create_time_place(event, -1, -1, False)

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
            image=SimpleUploadedFile(name='img.jpg', content='', content_type='image/jpeg'),
            publication_time=timezone.localtime() - timedelta(days=1),
        )
        self.event = Event.objects.create(
            title='FUTURE',
            image=SimpleUploadedFile(name='img.jpg', content='', content_type='image/jpeg'),
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
            image=SimpleUploadedFile(name='img.jpg', content='', content_type='image/jpeg'),
            publication_time=timezone.now() - timedelta(days=1),
            hidden=True,
            private=False,
        )
        self.event = Event.objects.create(
            title='',
            image=SimpleUploadedFile(name='img.jpg', content='', content_type='image/jpeg'),
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
        self.article.pub_date = timezone.now() + timedelta(days=1)
        response = self.client.get(reverse('article', kwargs={'pk': self.article.pk}))
        self.assertEqual(response.status_code, 404)
        self.add_permission('change_article')
        response = self.client.get(reverse('article', kwargs={'pk': self.article.pk}))
        self.assertEqual(response.status_code, 200)
