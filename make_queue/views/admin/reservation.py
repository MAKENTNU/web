from django.shortcuts import render
from django.views import View

from make_queue.models import Reservation


class AdminReservationView(View):
    template_name = "make_queue/reservations.html"

    def get(self, request):
        event_reservation = []
        for reservation_subclass in Reservation.__subclasses__():
            event_reservation.extend(reservation_subclass.objects.exclude(event=None, special=False))
        return render(request, self.template_name, {"reservations": event_reservation, "admin": True})