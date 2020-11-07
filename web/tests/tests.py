from django.conf import settings
from django.test import Client, TestCase
from django_hosts import reverse

from users.models import User


class UrlTests(TestCase):

    def setUp(self):
        username = "TEST_USER"
        password = "TEST_PASS"
        self.user = User.objects.create_user(username=username, password=password)

        self.anon_client = Client()
        self.user_client = Client()
        self.user_client.login(username=username, password=password)

    def test_index(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_about(self):
        response = self.client.get("/about/")
        self.assertEqual(response.status_code, 200)

    def test_set_language(self):
        response = self.anon_client.post(reverse("set_language"), {"language": "en"})
        self.assertRedirects(response, "/en/")
        response = self.anon_client.post(reverse("set_language"), {"language": "nb"})
        self.assertRedirects(response, "/")

        response = self.user_client.post(reverse("set_language"), {"language": "en"})
        self.assertRedirects(response, "/en/")
        response = self.user_client.post(reverse("set_language"), {"language": "nb"})
        self.assertRedirects(response, "/")

        # Previously indirectly caused decorating "set_language" with "permission_required" (see https://github.com/MAKENTNU/web/pull/297).
        # [This test can potentially be removed]
        self.user_client.get(reverse("home", host="internal", host_args=["internal"]),
                             HTTP_HOST=f"internal.{settings.PARENT_HOST}")
        # Should not redirect to login (caused by the above line)
        response = self.anon_client.post(reverse("set_language"), {"language": "en"})
        self.assertRedirects(response, "/en/")

# TODO: test views' logic
