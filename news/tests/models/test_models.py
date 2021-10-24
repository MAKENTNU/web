from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from ...models import Article, Event, TimePlace


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
