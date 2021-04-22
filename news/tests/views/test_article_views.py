import json
from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from users.models import User
from util.test_utils import MOCK_JPG_FILE
from ...models import Article


class ArticleViewTests(TestCase):

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

    def test_admin(self):
        response = self.client.get(reverse('admin_article_list'))
        self.assertNotEqual(response.status_code, 200)

        self.user.add_perms('news.change_article')
        response = self.client.get(reverse('admin_article_list'))
        self.assertEqual(response.status_code, 200)

    def test_articles(self):
        response = self.client.get(reverse('article_list'))
        self.assertEqual(response.status_code, 200)

    def test_article(self):
        response = self.client.get(reverse('article_detail', kwargs={'article': self.article}))
        self.assertEqual(response.status_code, 200)

    def test_article_create(self):
        response = self.client.get(reverse('article_create'))
        self.assertNotEqual(response.status_code, 200)

        self.user.add_perms('news.add_article')
        response = self.client.get(reverse('article_create'))
        self.assertEqual(response.status_code, 200)

    def test_article_edit(self):
        response = self.client.get(reverse('article_edit', kwargs={'article': self.article}))
        self.assertNotEqual(response.status_code, 200)

        self.user.add_perms('news.change_article')
        response = self.client.get(reverse('article_edit', kwargs={'article': self.article}))
        self.assertEqual(response.status_code, 200)

    def test_admin_article_toggle_view(self):
        def toggle(pk, attr):
            response = self.client.post(reverse('article_toggle', args=[pk]), {'toggle_attr': attr})
            self.assertEqual(response.status_code, 200)
            return json.loads(response.content)

        self.user.add_perms('news.change_article')
        self.assertEquals(toggle(self.article.pk, 'non_existant_attr'), {})

        hidden = self.article.hidden
        self.assertEquals(toggle(self.article.pk, 'hidden'), {'color': 'grey' if hidden else 'yellow'})
        self.assertEquals(toggle(self.article.pk, 'hidden'), {'color': 'yellow' if hidden else 'grey'})

    def test_private_article(self):
        response = self.client.get(reverse('article_detail', kwargs={'article': self.article}))
        self.assertEqual(response.status_code, 200)

        self.article.private = True
        self.article.save()
        response = self.client.get(reverse('article_detail', kwargs={'article': self.article}))
        self.assertGreaterEqual(response.status_code, 400)

        self.user.add_perms('news.can_view_private')
        response = self.client.get(reverse('article_detail', kwargs={'article': self.article}))
        self.assertEqual(response.status_code, 200)

    def test_not_published_article(self):
        self.article.publication_time = timezone.now() - timedelta(days=1)
        self.article.save()
        response = self.client.get(reverse('article_detail', kwargs={'article': self.article}))
        self.assertEqual(response.status_code, 200)

        self.article.publication_time = timezone.now() + timedelta(days=1)
        self.article.save()
        response = self.client.get(reverse('article_detail', kwargs={'article': self.article}))
        self.assertGreaterEqual(response.status_code, 400)

        self.user.add_perms('news.change_article')
        response = self.client.get(reverse('article_detail', kwargs={'article': self.article}))
        self.assertEqual(response.status_code, 200)

    def test_hidden_article(self):
        self.article.hidden = True
        self.article.save()
        response = self.client.get(reverse('article_detail', kwargs={'article': self.article}))
        self.assertGreaterEqual(response.status_code, 400)

        self.user.add_perms('news.change_article')
        response = self.client.get(reverse('article_detail', kwargs={'article': self.article}))
        self.assertEqual(response.status_code, 200)
