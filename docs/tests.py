from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from django_hosts import reverse

from users.models import User
from util.test_utils import assert_requesting_paths_succeeds
from .models import Content, Page


class UrlTests(TestCase):

    def setUp(self):
        self.user1 = User.objects.create_user("user1")
        now = timezone.localtime()
        self.page1 = Page.objects.create(
            title="Page 1",
            created_by=self.user1,
        )
        self.content1 = Content.objects.create(
            page=self.page1,
            changed=now - timedelta(days=1),
            content="Lorem ipsum dolor sit amet",
        )
        self.content2 = Content.objects.create(
            page=self.page1,
            changed=now,
            content="LoReM iPsUm DoLoR sIt aMeT",
            made_by=self.user1,
        )

    def test_all_get_request_paths_succeed(self):
        paths_to_must_be_authenticated = {
            self.reverse('home'): True,
            self.reverse('page', pk=self.page1): True,
            self.reverse('page-history', pk=self.page1): True,
            self.reverse('old-page-content', pk=self.page1, content=self.content1): True,
            self.reverse('old-page-content', pk=self.page1, content=self.content2): True,
            self.reverse('create-page'): True,
            self.reverse('edit-page', pk=self.page1): True,
            self.reverse('search-pages'): True,
            '/robots.txt': False,
        }
        assert_requesting_paths_succeeds(self, paths_to_must_be_authenticated, 'docs')

    @staticmethod
    def reverse(viewname: str, **kwargs):
        return reverse(viewname, kwargs=kwargs, host='docs')
