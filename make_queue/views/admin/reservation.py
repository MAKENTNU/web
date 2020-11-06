from django.views.generic import TemplateView

from ...models.models import Reservation


class AdminReservationView(TemplateView):
    """View to see all reservations that are either event reservations or MAKE NTNU reservations"""
    template_name = "make_queue/reservation_list.html"

    def get_context_data(self):
        """
        Retrieves all event reservations and MAKE NTNU reservations and sets admin mode for the template

        :return: The context required for the view
        """
        return {
            "reservations": Reservation.objects.exclude(event=None, special=False).order_by("-end_time", "-start_time"),
            "admin": True,
        }
