from django.views.generic import TemplateView

from ...models.models import Reservation


class MyReservationsView(TemplateView):
    """View for seeing the user's reservations."""
    template_name = 'make_queue/reservation_list.html'

    def get_context_data(self):
        """
        Creates a list of the user's reservations, that are not event reservations or MAKE NTNU's reservations.

        :return: A list of the user's reservations
        """
        return {
            "reservations": Reservation.objects.filter(user=self.request.user, event=None, special=False).order_by("-end_time", "-start_time"),
        }
