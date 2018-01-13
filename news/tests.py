from django.test import TestCase

from news.models import Article


class ModelTestCase(TestCase):
    def test_str(self):
        article = Article.objects.create(title='TEST_TITLE')
        self.assertEqual(article.title, 'TEST_TITLE')
        self.assertEqual(article.title, str(article))
