from datetime import timedelta

from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from users.models import User
from ...models.course import Printer3DCourse
from ...models.models import Machine, MachineType, Quota, Reservation


class DeleteReservationViewTestCase(TestCase):

    def setUp(self):
        password = "weak_pass"
        self.user1 = User.objects.create_user("user1", "user1@makentnu.no", password)
        self.user2 = User.objects.create_user("user2", "user2@makentnu.no", password)
        self.client1 = Client()
        self.client2 = Client()
        self.client1.login(username=self.user1.username, password=password)
        self.client2.login(username=self.user2.username, password=password)

        # See the `0015_machinetype.py` migration for which MachineTypes are created by default
        printer_machine_type = MachineType.objects.get(pk=1)
        self.machine1 = Machine.objects.create(
            name="U1", machine_model="Ultimaker 2", machine_type=printer_machine_type,
            location="MAKE", status=Machine.Status.AVAILABLE,
        )

        Quota.objects.create(user=self.user1, number_of_reservations=2, ignore_rules=True, machine_type=printer_machine_type)
        Quota.objects.create(user=self.user2, number_of_reservations=2, ignore_rules=True, machine_type=printer_machine_type)

        now = timezone.localtime()
        Printer3DCourse.objects.create(user=self.user1, username=self.user1.username, name=self.user1.get_full_name(), date=now)
        Printer3DCourse.objects.create(user=self.user2, username=self.user2.username, name=self.user2.get_full_name(), date=now)

        self.reservation = Reservation.objects.create(
            user=self.user1,
            machine=self.machine1,
            start_time=now + timedelta(hours=2),
            end_time=now + timedelta(hours=4),
        )

    def test_delete_single_reservation(self):
        response = self.client1.post(reverse('delete_reservation'),
                                     {'pk': self.reservation.pk})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Reservation.objects.filter(pk=self.reservation.pk).exists())

    def test_delete_other_users_reservation(self):
        response = self.client2.post(reverse('delete_reservation'),
                                     {'pk': self.reservation.pk})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Reservation.objects.filter(pk=self.reservation.pk).exists())

    def test_delete_one_of_users_reservations(self):
        now = timezone.localtime()
        reservation2 = Reservation.objects.create(
            user=self.user1,
            machine=self.machine1,
            start_time=now + timedelta(hours=6),
            end_time=now + timedelta(hours=8),
        )

        response = self.client1.post(reverse('delete_reservation'),
                                     {'pk': self.reservation.pk})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Reservation.objects.filter(pk=self.reservation.pk).exists())
        self.assertTrue(Reservation.objects.filter(pk=reservation2.pk).exists())
