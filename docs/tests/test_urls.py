from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from django_hosts import reverse

from users.models import User
from util.test_utils import Get, assert_requesting_paths_succeeds
from ..models import Content, Page


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
        path_predicates = [
            Get(self.reverse('home'), public=False),
            Get(self.reverse('page_detail', pk=self.page1), public=False),
            Get(self.reverse('page_history', pk=self.page1), public=False),
            Get(self.reverse('old_page_content', pk=self.page1, content=self.content1), public=False),
            Get(self.reverse('old_page_content', pk=self.page1, content=self.content2), public=False),
            Get(self.reverse('create_page'), public=False),
            Get(self.reverse('edit_page', pk=self.page1), public=False),
            Get(self.reverse('search_pages'), public=False),
            Get('/robots.txt', public=True, translated=False),
            Get('/.well-known/security.txt', public=True, translated=False),
        ]
        assert_requesting_paths_succeeds(self, path_predicates, 'docs')

    @staticmethod
    def reverse(viewname: str, **kwargs):
        return reverse(viewname, kwargs=kwargs, host='docs')
