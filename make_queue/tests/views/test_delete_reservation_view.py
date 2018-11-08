from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse

from make_queue.fields import MachineTypeField
from make_queue.models.course import Printer3DCourse
from make_queue.models.models import Machine, Reservation, Quota


class DeleteReservationViewTestCase(TestCase):

    def setUp(self):
        user1 = User.objects.create_user("user1", "user1@makentnu.no", "weak_pass")
        user1.save()
        user2 = User.objects.create_user("user2", "user2@makentnu.no", "weak_pass")
        user2.save()

        machine_type_printer = MachineTypeField.get_machine_type(1)
        Machine.objects.create(name="U1", location="Make", machine_model="Ultimaker 2", status="F",
                               machine_type=machine_type_printer)

        Quota.objects.create(user=user1, number_of_reservations=2, ignore_rules=True, machine_type=machine_type_printer)
        Quota.objects.create(user=user2, number_of_reservations=2, ignore_rules=True, machine_type=machine_type_printer)

        Printer3DCourse.objects.create(user=user1, username=user1.username, name=user1.get_full_name(),
                                       date=timezone.now())
        Printer3DCourse.objects.create(user=user2, username=user2.username, name=user2.get_full_name(),
                                       date=timezone.now())

        self.reservation = Reservation.objects.create(user=user1,
                                                      machine=Machine.objects.get(name="U1"),
                                                      start_time=timezone.now() + timezone.timedelta(hours=2),
                                                      end_time=timezone.now() + timezone.timedelta(hours=4),
                                                      event=None)

    def test_delete_single_reservation(self):
        self.client.login(username="user1", password="weak_pass")
        response = self.client.post(reverse('delete_reservation'),
                                    {'pk': self.reservation.pk})
        self.assertEqual(302, response.status_code)
        self.assertFalse(Reservation.objects.filter(pk=self.reservation.pk).exists())

    def test_delete_other_users_reservation(self):
        self.client.login(username="user2", password="weak_pass")
        response = self.client.post(reverse('delete_reservation'),
                                    {'pk': self.reservation.pk})
        self.assertEqual(302, response.status_code)
        self.assertTrue(Reservation.objects.filter(pk=self.reservation.pk).exists())

    def test_delete_one_of_users_reservations(self):
        reservation2 = Reservation.objects.create(user=User.objects.get(username="user1"),
                                                  machine=Machine.objects.get(name="U1"),
                                                  start_time=timezone.now() + timezone.timedelta(hours=6),
                                                  end_time=timezone.now() + timezone.timedelta(hours=8),
                                                  event=None)

        self.client.login(username="user1", password="weak_pass")
        response = self.client.post(reverse('delete_reservation'),
                                    {'pk': self.reservation.pk})
        self.assertEqual(302, response.status_code)
        self.assertFalse(Reservation.objects.filter(pk=self.reservation.pk).exists())
        self.assertTrue(Reservation.objects.filter(pk=reservation2.pk).exists())
