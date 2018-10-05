from django.views.generic import TemplateView

from make_queue.models.models import Reservation


class AdminReservationView(TemplateView):
    """View to see all reservations that are either event reservations or MAKE NTNU reservations"""
    template_name = "make_queue/reservations.html"

    def get_context_data(self):
        """
        Retrieves all event reservations and MAKE NTNU reservations and sets admin mode for the template

        :return: The context required for the view
        """
        return {"reservations": [event_reservation for reservation_subclass in Reservation.__subclasses__() for
                                 event_reservation in reservation_subclass.objects.exclude(event=None, special=False)],
                "admin": True}
