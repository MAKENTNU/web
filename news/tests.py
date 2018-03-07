from datetime import timedelta

from django.contrib.auth.models import User, Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from news.models import Article, Event, TimePlace


class ModelTestCase(TestCase):
    def test_str(self):
        article = Article.objects.create(title='TEST_TITLE')
        self.assertEqual(article.title, 'TEST_TITLE')
        self.assertEqual(article.title, str(article))

    def test_article_manager(self):
        Article.objects.create(
            title='NOT PUBLISHED',
            pub_date=timezone.now() + timedelta(days=1),
            pub_time=timezone.now().time()
        )
        Article.objects.create(
            title='NOT PUBLISHED',
            pub_date=timezone.now(),
            pub_time=(timezone.now() + timedelta(seconds=1)).time()
        )
        Article.objects.create(
            title='PUBLISHED',
            pub_date=timezone.now() - timedelta(days=1),
            pub_time=timezone.now().time()
        )
        Article.objects.create(
            title='PUBLISHED',
            pub_date=timezone.now(),
            pub_time=(timezone.now() - timedelta(seconds=1)).time()
        )
        self.assertEqual(Article.objects.published().count(), 2)
        self.assertEqual(list(Article.objects.published().values_list('title', flat=True)), ['PUBLISHED'] * 2)

    def test_event_manager(self):
        event = Event.objects.create(title='', hidden=False)
        hidden_event = Event.objects.create(title='', hidden=True)
        not_published = TimePlace.objects.create(
            event=event,
            pub_date=timezone.now() + timedelta(days=1),
            start_date=timezone.now(),
            start_time=(timezone.now() + timedelta(seconds=1)).time()
        )
        future = TimePlace.objects.create(
            event=event,
            pub_date=timezone.now() - timedelta(days=1),
            start_date=timezone.now(),
            start_time=(timezone.now() + timedelta(seconds=1)).time(),
            hidden=False,
        )
        past = TimePlace.objects.create(
            event=event,
            pub_date=timezone.now() - timedelta(days=1),
            start_date=timezone.now(),
            start_time=(timezone.now() - timedelta(seconds=1)).time(),
            hidden=False,
        )
        TimePlace.objects.create(
            event=hidden_event,
            pub_date=timezone.now() - timedelta(days=1),
            start_date=timezone.now(),
            start_time=(timezone.now() + timedelta(seconds=1)).time()
        )
        TimePlace.objects.create(
            event=hidden_event,
            pub_date=timezone.now() - timedelta(days=1),
            start_date=timezone.now(),
            start_time=(timezone.now() - timedelta(seconds=1)).time()
        )
        TimePlace.objects.create(
            event=hidden_event,
            pub_date=timezone.now() - timedelta(days=1),
            start_date=timezone.now(),
            start_time=(timezone.now() + timedelta(seconds=1)).time(),
            hidden=False,
        )
        TimePlace.objects.create(
            event=hidden_event,
            pub_date=timezone.now() - timedelta(days=1),
            start_date=timezone.now(),
            start_time=(timezone.now() - timedelta(seconds=1)).time(),
            hidden=False,
        )
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
            pub_date=timezone.now() - timedelta(days=1),
            pub_time=timezone.now().time()
        )
        self.event = Event.objects.create(
            title='FUTURE',
            image=SimpleUploadedFile(name='img.jpg', content='', content_type='image/jpeg'),
        )

    def test_admin(self):
        response = self.client.get(reverse('admin'))
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
