from django.test import TestCase

from contentbox.models import ContentBox


class ModelTestCase(TestCase):
    def test_str(self):
        contentbox = ContentBox.objects.create(title='TEST_TITLE')
        self.assertEqual(contentbox.title, 'TEST_TITLE')
        self.assertEqual(contentbox.title, str(contentbox))
