from django.views.generic import ListView

from ...models.models import Reservation


class AdminReservationView(ListView):
    """View to see all reservations that are either event reservations or MAKE NTNU's reservations."""
    model = Reservation
    queryset = Reservation.objects.exclude(event=None, special=False).order_by('-end_time', '-start_time')
    template_name = 'make_queue/reservation_list.html'
    context_object_name = 'reservations'
    extra_context = {
        'is_MAKE': True,
    }
