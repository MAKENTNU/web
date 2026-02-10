import json
from datetime import timedelta
from http import HTTPStatus

from django.test import TestCase
from django.utils import timezone
from django_hosts import reverse

from users.models import User
from util.test_utils import CleanUpTempFilesTestMixin, MOCK_JPG_FILE
from ...models import Article


class ArticleViewTests(CleanUpTempFilesTestMixin, TestCase):
    def setUp(self):
        username = "TEST_USER"
        password = "TEST_PASS"
        self.user = User.objects.create_user(username=username, password=password)
        self.client.login(username=username, password=password)

        self.article = Article.objects.create(
            title="PUBLISHED",
            image=MOCK_JPG_FILE,
            image_description="Mock image",
            publication_time=timezone.localtime() - timedelta(days=1),
        )
        self.article_url = self.article.get_absolute_url()

    def test_admin_article_list_view(self):
        response = self.client.get(reverse("admin_article_list"))
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

        self.user.add_perms("internal.is_internal", "news.change_article")
        response = self.client.get(reverse("admin_article_list"))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_article_create_view(self):
        response = self.client.get(reverse("article_create"))
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

        self.user.add_perms("internal.is_internal", "news.add_article")
        response = self.client.get(reverse("article_create"))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_article_update_view(self):
        response = self.client.get(reverse("article_update", args=[self.article.pk]))
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

        self.user.add_perms("internal.is_internal", "news.change_article")
        response = self.client.get(reverse("article_update", args=[self.article.pk]))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_admin_api_article_toggle_view(self):
        def toggle(pk, attr):
            response = self.client.post(
                reverse("admin_api_article_toggle", args=[pk]), {"toggle_attr": attr}
            )
            self.assertEqual(response.status_code, HTTPStatus.OK)
            return json.loads(response.content)

        self.user.add_perms("internal.is_internal", "news.change_article")
        self.assertDictEqual(toggle(self.article.pk, "non_existent_attr"), {})

        self.assertDictEqual(toggle(self.article.pk, "hidden"), {"is_hidden": True})
        self.assertDictEqual(toggle(self.article.pk, "hidden"), {"is_hidden": False})

    def test_private_article(self):
        response = self.client.get(self.article_url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

        self.article.private = True
        self.article.save()
        response = self.client.get(self.article_url)
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

        self.user.add_perms("news.can_view_private")
        response = self.client.get(self.article_url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_not_published_article(self):
        self.article.publication_time = timezone.now() - timedelta(days=1)
        self.article.save()
        response = self.client.get(self.article_url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

        self.article.publication_time = timezone.now() + timedelta(days=1)
        self.article.save()
        response = self.client.get(self.article_url)
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

        self.user.add_perms("news.change_article")
        response = self.client.get(self.article_url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_hidden_article(self):
        self.article.hidden = True
        self.article.save()
        response = self.client.get(self.article_url)
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

        self.user.add_perms("news.change_article")
        response = self.client.get(self.article_url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
