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

        printer_machine_type = MachineType.objects.get(pk=1)
        Machine.objects.create(name="U1", location="Make", machine_model="Ultimaker 2", status=Machine.Status.AVAILABLE,
                               machine_type=printer_machine_type)

        Quota.objects.create(user=self.user1, number_of_reservations=2, ignore_rules=True, machine_type=printer_machine_type)
        Quota.objects.create(user=self.user2, number_of_reservations=2, ignore_rules=True, machine_type=printer_machine_type)

        Printer3DCourse.objects.create(user=self.user1, username=self.user1.username, name=self.user1.get_full_name(),
                                       date=timezone.now())
        Printer3DCourse.objects.create(user=self.user2, username=self.user2.username, name=self.user2.get_full_name(),
                                       date=timezone.now())

        self.reservation = Reservation.objects.create(user=self.user1,
                                                      machine=Machine.objects.get(name="U1"),
                                                      start_time=timezone.now() + timezone.timedelta(hours=2),
                                                      end_time=timezone.now() + timezone.timedelta(hours=4),
                                                      event=None)

    def test_delete_single_reservation(self):
        response = self.client1.post(reverse('delete_reservation'),
                                     {'pk': self.reservation.pk})
        self.assertEqual(302, response.status_code)
        self.assertFalse(Reservation.objects.filter(pk=self.reservation.pk).exists())

    def test_delete_other_users_reservation(self):
        response = self.client2.post(reverse('delete_reservation'),
                                     {'pk': self.reservation.pk})
        self.assertEqual(302, response.status_code)
        self.assertTrue(Reservation.objects.filter(pk=self.reservation.pk).exists())

    def test_delete_one_of_users_reservations(self):
        reservation2 = Reservation.objects.create(user=User.objects.get(username=self.user1.username),
                                                  machine=Machine.objects.get(name="U1"),
                                                  start_time=timezone.now() + timezone.timedelta(hours=6),
                                                  end_time=timezone.now() + timezone.timedelta(hours=8),
                                                  event=None)

        response = self.client1.post(reverse('delete_reservation'),
                                     {'pk': self.reservation.pk})
        self.assertEqual(302, response.status_code)
        self.assertFalse(Reservation.objects.filter(pk=self.reservation.pk).exists())
        self.assertTrue(Reservation.objects.filter(pk=reservation2.pk).exists())
