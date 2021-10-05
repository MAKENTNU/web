from django.test import TestCase
from django_hosts import reverse

from util.test_utils import Get, MOCK_JPG_FILE, assert_requesting_paths_succeeds
from ..models import Equipment


class UrlTests(TestCase):

    def setUp(self):
        self.equipment1 = Equipment.objects.create(
            title="Test equipment 1",
            description="Lorem ipsum dolor sit amet",
            image=MOCK_JPG_FILE,
        )

    def test_all_get_request_paths_succeed(self):
        path_predicates = [
            Get(reverse('makerspace'), public=True),
            Get(reverse('makerspace-equipment-list'), public=True),
            Get(reverse('makerspace-equipment-admin'), public=False),
            Get(reverse('makerspace-equipment-create'), public=False),
            Get(reverse('makerspace-equipment-edit', kwargs={'pk': self.equipment1.pk}), public=False),
            Get(reverse('makerspace-equipment', kwargs={'pk': self.equipment1.pk}), public=True),
            Get(reverse('rules'), public=True),
        ]
        assert_requesting_paths_succeeds(self, path_predicates)
