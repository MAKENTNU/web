from django.test import TestCase
from django_hosts import reverse

from util.test_utils import Get, MOCK_JPG_FILE, assert_requesting_paths_succeeds
from ..models import Committee, InheritanceGroup


class UrlTests(TestCase):

    def setUp(self):
        self.group1 = InheritanceGroup.objects.create(name="Group 1")
        self.committee1 = Committee.objects.create(
            group=self.group1,
            description="Lorem ipsum dolor sit amet",
            email="committee1@makentnu.no",
            image=MOCK_JPG_FILE,
            clickbait="Wow!",
        )

    def test_all_get_request_paths_succeed(self):
        path_predicates = [
            Get(reverse('committee_list'), public=True),
            Get(reverse('committee_detail', kwargs={'pk': self.committee1.pk}), public=True),
            Get(reverse('committee_edit', kwargs={'pk': self.committee1.pk}), public=False),
            Get(reverse('committee_admin'), public=False),
        ]
        assert_requesting_paths_succeeds(self, path_predicates)
