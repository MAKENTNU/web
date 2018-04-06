from django.views.generic import TemplateView

from make_queue.models import Reservation


class MyReservationsView(TemplateView):
    """View for seeing the users reservations"""
    template_name = "make_queue/reservations.html"

    def get_context_data(self):
        """
        Creates a list of the user's reservations, that are not event reservations or MAKE NTNU reservations

        :return: A list of the user's reservations
        """
        return {"reservations": sorted(
            [reservation for reservation_subclass in Reservation.__subclasses__() for reservation in
             reservation_subclass.objects.filter(user=self.request.user, event=None, special=False)],
            key=lambda x: x.end_time, reverse=True)}
