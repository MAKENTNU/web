from django.views.generic import TemplateView

from ...models.models import Reservation


class AdminReservationView(TemplateView):
    """View to see all reservations that are either event reservations or MAKE NTNU's reservations."""
    template_name = 'make_queue/reservation_list.html'
    extra_context = {
        # Retrieves all event reservations and MAKE NTNU's reservations and sets admin mode for the template
        "reservations": Reservation.objects.exclude(event=None, special=False).order_by("-end_time", "-start_time"),
        "admin": True,
    }
