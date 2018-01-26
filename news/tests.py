from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from news.models import Article, Event


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
        self.assertEqual(list(Article.objects.published().values_list('title', flat=True)), ['PUBLISHED']*2)

    def test_event_manager(self):
        Event.objects.create(
            title='NOT PUBLISHED',
            pub_date=timezone.now() + timedelta(days=1),
            start_date=timezone.now(),
            start_time=(timezone.now() + timedelta(seconds=1)).time()
        )
        Event.objects.create(
            title='FUTURE',
            pub_date=timezone.now() - timedelta(days=1),
            start_date=timezone.now(),
            start_time=(timezone.now() + timedelta(seconds=1)).time()
        )
        Event.objects.create(
            title='PAST',
            pub_date=timezone.now() - timedelta(days=1),
            start_date=timezone.now(),
            start_time=(timezone.now() - timedelta(seconds=1)).time()
        )
        self.assertEqual(Event.objects.future().count(), 1)
        self.assertEqual(Event.objects.past().count(), 1)
        self.assertEqual(Event.objects.future().first().title, 'FUTURE')
        self.assertEqual(Event.objects.past().first().title, 'PAST')
