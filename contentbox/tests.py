from django.test import TestCase

from contentbox.models import ContentBox, DisplayContentBoxView


class ModelTestCase(TestCase):
    def test_str(self):
        contentbox = ContentBox.objects.create(title='TEST_TITLE')
        self.assertEqual(contentbox.title, 'TEST_TITLE')
        self.assertEqual(contentbox.title, str(contentbox))

    def test_get(self):
        self.assertEqual(ContentBox.objects.count(), 0)
        contentbox = ContentBox.get(title='TEST_TITLE')
        self.assertEqual(ContentBox.objects.count(), 1)
        self.assertEqual(contentbox.title, 'TEST_TITLE')

        contentbox2 = ContentBox.get(title='TEST_TITLE')
        self.assertEqual(ContentBox.objects.count(), 1)
        self.assertEqual(contentbox, contentbox2)

    def test_display_view(self):
        view = DisplayContentBoxView()
        view.title = 'TEST_TITLE'
        context = view.get_context_data()
        self.assertTrue('contentbox' in context)
        self.assertEqual(context['contentbox'].title, 'TEST_TITLE')

    def test_edit(self):
        ContentBox.get(title='TEST_TITLE')
        response = self.client.get('/contentbox/1/edit/')
        self.assertEqual(response.status_code, 200)
