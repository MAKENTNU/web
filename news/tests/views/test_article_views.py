import json
from datetime import timedelta
from http import HTTPStatus

from django.urls import reverse
from django.utils import timezone

from users.models import User
from util.test_utils import MOCK_JPG_FILE, PermissionsTestCase
from ...models import Article


class ArticleViewTests(PermissionsTestCase):

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
        self.assertNotEqual(response.status_code, HTTPStatus.OK)

        self.add_permissions(self.user, 'change_article')
        response = self.client.get(reverse('admin_article_list'))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_articles(self):
        response = self.client.get(reverse('article_list'))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_article(self):
        response = self.client.get(reverse('article_detail', kwargs={'pk': self.article.pk}))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_article_create(self):
        response = self.client.get(reverse('article_create'))
        self.assertNotEqual(response.status_code, HTTPStatus.OK)

        self.add_permissions(self.user, 'add_article')
        response = self.client.get(reverse('article_create'))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_article_edit(self):
        response = self.client.get(reverse('article_edit', kwargs={'pk': self.article.pk}))
        self.assertNotEqual(response.status_code, HTTPStatus.OK)

        self.add_permissions(self.user, 'change_article')
        response = self.client.get(reverse('article_edit', kwargs={'pk': self.article.pk}))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_admin_article_toggle_view(self):
        def toggle(pk, attr):
            response = self.client.post(reverse('article_toggle'), {'pk': pk, 'toggle': attr})
            self.assertEqual(response.status_code, HTTPStatus.OK)
            return json.loads(response.content)

        self.add_permissions(self.user, 'change_article')
        self.assertEquals(toggle(-1, 'hidden'), {})
        self.assertEquals(toggle(self.article.pk, 'ajfal'), {})

        hidden = self.article.hidden
        self.assertEquals(toggle(self.article.pk, 'hidden'), {'color': 'grey' if hidden else 'yellow'})
        self.assertEquals(toggle(self.article.pk, 'hidden'), {'color': 'yellow' if hidden else 'grey'})

    def test_private_article(self):
        response = self.client.get(reverse('article_detail', kwargs={'pk': self.article.pk}))
        self.assertEqual(response.status_code, HTTPStatus.OK)

        self.article.private = True
        self.article.save()
        response = self.client.get(reverse('article_detail', kwargs={'pk': self.article.pk}))
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

        self.add_permissions(self.user, 'can_view_private')
        response = self.client.get(reverse('article_detail', kwargs={'pk': self.article.pk}))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_not_published_article(self):
        self.article.publication_time = timezone.now() - timedelta(days=1)
        self.article.save()
        response = self.client.get(reverse('article_detail', kwargs={'pk': self.article.pk}))
        self.assertEqual(response.status_code, HTTPStatus.OK)

        self.article.publication_time = timezone.now() + timedelta(days=1)
        self.article.save()
        response = self.client.get(reverse('article_detail', kwargs={'pk': self.article.pk}))
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

        self.add_permissions(self.user, 'change_article')
        response = self.client.get(reverse('article_detail', kwargs={'pk': self.article.pk}))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_hidden_article(self):
        self.article.hidden = True
        self.article.save()
        response = self.client.get(reverse('article_detail', kwargs={'pk': self.article.pk}))
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

        self.add_permissions(self.user, 'change_article')
        response = self.client.get(reverse('article_detail', kwargs={'pk': self.article.pk}))
        self.assertEqual(response.status_code, HTTPStatus.OK)
