from django.test import TestCase
from django_hosts import reverse

from util.test_utils import MOCK_JPG_FILE, assert_requesting_paths_succeeds
from .models import Equipment


class UrlTests(TestCase):

    def setUp(self):
        self.equipment1 = Equipment.objects.create(
            title="Test equipment 1",
            description="Lorem ipsum dolor sit amet",
            image=MOCK_JPG_FILE,
        )

    def test_all_get_request_paths_succeed(self):
        paths_to_must_be_authenticated = {
            reverse('makerspace'): False,
            reverse('makerspace-equipment-list'): False,
            reverse('makerspace-equipment-admin'): True,
            reverse('makerspace-equipment-create'): True,
            reverse('makerspace-equipment-edit', kwargs={'pk': self.equipment1.pk}): True,
            reverse('makerspace-equipment', kwargs={'pk': self.equipment1.pk}): False,
            reverse('rules'): False,
        }
        assert_requesting_paths_succeeds(self, paths_to_must_be_authenticated)
