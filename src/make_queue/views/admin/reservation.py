from django.contrib.auth.mixins import PermissionRequiredMixin
from django.views.generic import ListView

from ...models.reservation import Reservation


class MAKEReservationsListView(PermissionRequiredMixin, ListView):
    """View to see all reservations that are either event reservations or MAKE NTNU's reservations."""
    permission_required = ('make_queue.can_create_event_reservation',)
    model = Reservation
    queryset = Reservation.objects.exclude(event=None, special=False).order_by('-end_time', '-start_time')
    template_name = 'make_queue/reservation_list.html'
    context_object_name = 'reservations'
    extra_context = {
        'is_MAKE': True,
    }
