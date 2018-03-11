from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from make_queue.models import Quota3D, Reservation3D, Printer3D, SewingMachine, QuotaSewing, ReservationSewing
from make_queue.views.reservation.overview import MyReservationsView


class MyReservationsViewTestCase(TestCase):

    def setUp(self):
        user = User.objects.create_user("user", "user@makentnu.no")
        user.save()

        printer = Printer3D.objects.create(name="U1", model="Ultimaker 2", location="S1", status="F")
        Quota3D.objects.create(user=user, max_number_of_reservations=2, max_time_reservation=10, can_print=True)

        Reservation3D.objects.create(user=user, machine=printer, event=None,
                                     start_time=timezone.now(), end_time=timezone.now() + timezone.timedelta(hours=2))

    def test_get_user_reservations_single_reservation(self):
        self.assertEqual([Reservation3D.objects.get(user=User.objects.get(username="user"))],
                         MyReservationsView.get_user_reservations(User.objects.get(username="user")))

    def test_get_user_reservations_multiple_reservations(self):
        Reservation3D.objects.create(user=User.objects.get(username="user"),
                                     machine=Printer3D.objects.get(name="U1"),
                                     start_time=timezone.now() - timezone.timedelta(hours=4),
                                     end_time=timezone.now() - timezone.timedelta(hours=2), event=None)

        self.assertEqual(
            list(Reservation3D.objects.filter(user=User.objects.get(username="user")).order_by("-start_time")),
            MyReservationsView.get_user_reservations(User.objects.get(username="user")))

    def test_get_user_reservations_different_types(self):
        QuotaSewing.objects.create(user=User.objects.get(username="user"), max_number_of_reservations=2,
                                   max_time_reservation=10)

        sewing_machine = SewingMachine.objects.create(name="T1", model="Generic", location="M1", status="F")

        ReservationSewing.objects.create(user=User.objects.get(username="user"), machine=sewing_machine,
                                         start_time=timezone.now(),
                                         end_time=timezone.now() + timezone.timedelta(hours=2), event=None)

        self.assertEqual([ReservationSewing.objects.get(user=User.objects.get(username="user")),
                          Reservation3D.objects.get(user=User.objects.get(username="user"))],
                         MyReservationsView.get_user_reservations(User.objects.get(username="user")))
