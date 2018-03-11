from django.shortcuts import render
from django.views import View

from make_queue.models import Reservation


class MyReservationsView(View):
    template_name = "make_queue/reservations.html"

    @staticmethod
    def get_user_reservations(user):
        user_reservations = []
        for reservation_subclass in Reservation.__subclasses__():
            user_reservations.extend(reservation_subclass.objects.filter(user=user, event=None, special=False))
        return sorted(user_reservations, key=lambda x: x.end_time, reverse=True)

    def get(self, request):
        return render(request, self.template_name, {'reservations': self.get_user_reservations(request.user)})
