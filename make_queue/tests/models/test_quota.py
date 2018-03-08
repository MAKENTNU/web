from django.test import TestCase

from make_queue.models import Quota3D, Printer3D, Quota, SewingMachine
from django.contrib.auth.models import User


class TestQuota(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="test")
        self.printerQuota = Quota3D.objects.create(user=self.user)

    def test_get_quota_by_machine(self):
        self.assertEquals(Quota.get_quota_by_machine(Printer3D.literal, self.user), self.printerQuota)
        self.assertIsNotNone(Quota.get_quota_by_machine(SewingMachine.literal, self.user))

        try:
            Quota.get_quota_by_machine("", self.user)
            self.fail("Giving an illegal literal should throw an StopIteration Exception")
        except StopIteration:
            pass

    def test_to_string(self):
        self.assertEqual(str(self.printerQuota), "User test, can not print")
        self.printerQuota.can_print = True
        self.assertEqual(str(self.printerQuota), "User test, can print")
