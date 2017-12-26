from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse
from make_queue.models import Printer3D, Reservation3D, Quota3D


class DeleteReservationViewTestCase(TestCase):

    def setUp(self):
        user1 = User.objects.create_user("user1", "user1@makentnu.no", "weak_pass")
        user1.save()
        user2 = User.objects.create_user("user2", "user2@makentnu.no", "weak_pass")
        user2.save()

        Printer3D.objects.create(name="U1", location="Make", model="Ultimaker 2", status="F")

        Quota3D.objects.create(user=user1, max_time_reservation=10, max_number_of_reservations=2, can_print=True)
        Quota3D.objects.create(user=user2, max_time_reservation=10, max_number_of_reservations=2, can_print=True)

        self.reservation = Reservation3D.objects.create(user=user1,
                                                        machine=Printer3D.objects.get(name="U1"),
                                                        start_time=timezone.now() + timezone.timedelta(hours=2),
                                                        end_time=timezone.now() + timezone.timedelta(hours=4),
                                                        event=False)

    def test_delete_single_reservation(self):
        self.client.login(username="user1", password="weak_pass")
        response = self.client.post(reverse('delete_reservation'),
                                    {'pk': self.reservation.pk, 'machine_type': Printer3D.literal})
        self.assertEqual(302, response.status_code)
        self.assertFalse(Reservation3D.objects.filter(pk=self.reservation.pk).exists())

    def test_delete_other_users_reservation(self):
        self.client.login(username="user2", password="weak_pass")
        response = self.client.post(reverse('delete_reservation'),
                                    {'pk': self.reservation.pk, 'machine_type': Printer3D.literal})
        self.assertEqual(302, response.status_code)
        self.assertTrue(Reservation3D.objects.filter(pk=self.reservation.pk).exists())

    def test_delete_one_of_users_reservations(self):
        reservation2 = Reservation3D.objects.create(user=User.objects.get(username="user1"),
                                                    machine=Printer3D.objects.get(name="U1"),
                                                    start_time=timezone.now() + timezone.timedelta(hours=6),
                                                    end_time=timezone.now() + timezone.timedelta(hours=8),
                                                    event=False)

        self.client.login(username="user1", password="weak_pass")
        response = self.client.post(reverse('delete_reservation'),
                                    {'pk': self.reservation.pk, 'machine_type': Printer3D.literal})
        self.assertEqual(302, response.status_code)
        self.assertFalse(Reservation3D.objects.filter(pk=self.reservation.pk).exists())
        self.assertTrue(Reservation3D.objects.filter(pk=reservation2.pk).exists())

    def test_delete_old_reservation(self):
        reservation2 = Reservation3D.objects.create(user=User.objects.get(username="user1"),
                                                    machine=Printer3D.objects.get(name="U1"),
                                                    start_time=timezone.now() - timezone.timedelta(hours=6),
                                                    end_time=timezone.now() - timezone.timedelta(hours=4),
                                                    event=False)

        self.client.login(username="user1", password="weak_pass")
        response = self.client.post(reverse('delete_reservation'),
                                    {'pk': self.reservation.pk, 'machine_type': Printer3D.literal})
        self.assertEqual(302, response.status_code)
        self.assertTrue(Reservation3D.objects.filter(pk=reservation2.pk).exists())
