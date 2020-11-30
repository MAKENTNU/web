from django.db.models import Q
from django.views.generic import ListView

from ...models.models import Reservation


class MyReservationsView(ListView):
    """View for seeing the user's reservations"""
    model = Reservation
    template_name = "make_queue/reservations.html"
    context_object_name = 'reservations'

    def get_queryset(self):
        filter_query = Q(user=self.request.user)
        if not self.request.user.has_perm('make_queue.can_create_event_reservation'):
            filter_query &= Q(event=None, special=False)
        return Reservation.objects.filter(filter_query).order_by('-end_time', '-start_time')
