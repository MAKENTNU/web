from abc import ABCMeta

from django.db.models import Q
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import RedirectView, TemplateView

from make_queue.forms import ReservationForm
from make_queue.models import Quota, Machine, Reservation
from make_queue.templatetags.reservation_extra import calendar_url_reservation
from news.models import TimePlace


class ReservationCreateOrChangeView(TemplateView):
    """Base abstract class for the reservation create or change view"""
    __metaclass__ = ABCMeta
    template_name = "make_queue/make_reservation.html"

    def get_error_message(self, form):
        """
        Generates the correct error message for the given form
        :param form: The form to generate an error message
        :return: The error message
        """
        if self.request.user.has_perm("make_queue.can_create_event_reservation") and form.cleaned_data["event"]:
            return "Tidspunktet eller eventen, er ikke lengre tilgjengelig"
        return "Tidspunktet er ikke lengre tilgjengelig"

    def validate_and_save(self, reservation, form):
        """
        Tries to validate and save the given reservation
        :param reservation: The reservation to validate and save
        :param form: The form used to create/change the reservation
        :return: Either a redirect to the new/changed reservation in the calendar or an error message indicating why
                    the reservation cannot be validated
        """
        if not reservation.validate():
            context_data = self.get_context_data(reservation=reservation)
            context_data["error"] = self.get_error_message(form)
            return render(self.request, self.template_name, context_data)

        reservation.save()
        return redirect(calendar_url_reservation(reservation))

    def get_context_data(self, **kwargs):
        """
        Creates the context data required for the make reservation template. If reservation is given as a keyword
        argument, the view is made for that reservation
        :param kwargs: The request arguments for creating the context data
        :return: The context data needed for the template
        """

        # Always include a list of events and machines to populate the dropdown lists
        context_data = {
            "new_reservation": self.new_reservation, "events": list(TimePlace.objects.filter(
                Q(end_date=timezone.now().date(), end_time__gt=timezone.now().time()) |
                Q(end_date__gt=timezone.now().date()))),
            "machine_types": [
                {"literal": sub_class.literal, "instances": list(sub_class.objects.all())}
                for sub_class in Machine.__subclasses__() if
                Quota.get_quota_by_machine(sub_class.literal, self.request.user).can_make_new_reservation() and
                sub_class.objects.exists()
            ]
        }

        # If we are given a reservation, populate the information relevant to that reservation
        if "reservation" in kwargs:
            reservation = kwargs["reservation"]
            context_data["start_time"] = reservation.start_time
            context_data["end_time"] = reservation.end_time
            context_data["selected_machine"] = reservation.get_machine()
            context_data["event"] = reservation.event
            context_data["special"] = reservation.special
            context_data["special_text"] = reservation.special_text
            context_data["quota"] = reservation.get_quota()
        # Otherwise populate with default information given to the view
        else:
            context_data["selected_machine"] = kwargs["machine"]
            if "start_time" in kwargs:
                context_data["start_time"] = kwargs["start_time"]
            context_data["quota"] = Quota.get_quota_by_machine(kwargs["machine"].literal, self.request.user)

        return context_data

    def dispatch(self, request, *args, **kwargs):
        """
        If the request is a post request use the handle_post method, otherwise use the default method of the template
        view
        :param request: The HTTP request
        :return: HTTP response
        """
        if request.method == "POST":
            return self.handle_post(request, **kwargs)
        return super().dispatch(request, *args, **kwargs)

    def handle_post(self, request, **kwargs):
        """
        Handles and validates update requests
        :param request: The HTTP request
        """
        try:
            form = ReservationForm(request.POST)
            if form.is_valid():
                return self.form_valid(form, **kwargs)
        except Exception:
            pass
        return self.get(request, **kwargs)


class MakeReservationView(ReservationCreateOrChangeView):
    """View for creating a new reservation"""
    new_reservation = True

    def form_valid(self, form, **kwargs):
        """
        Creates a reservation from a valid ReservationForm
        :param form: The valid reservation form
        :return: HTTP response
        """
        reservation_type = Reservation.get_reservation_type(form.cleaned_data["machine_type"])

        reservation = reservation_type(start_time=form.cleaned_data["start_time"],
                                       end_time=form.cleaned_data["end_time"], user=self.request.user,
                                       machine=form.cleaned_data["machine"])

        if form.cleaned_data["event"]:
            reservation.event = form.cleaned_data["event"]

        if form.cleaned_data["special"]:
            reservation.special = True
            reservation.special_text = form.cleaned_data["special_text"]

        return self.validate_and_save(reservation, form)


class DeleteReservationView(RedirectView):
    """View for deleting a reservation (Cannot be DeleteView due to the abstract inheritance of reservations)"""
    http_method_names = ["post"]

    def get_redirect_url(self, *args, **kwargs):
        """
        Gives the redirect url for when the reservation is deleted
        :return: The redirect url
        """
        if "next" in self.request.POST:
            return self.request.POST.get("next")
        return reverse("my_reservations")

    def dispatch(self, request, *args, **kwargs):
        """
        Delete the reservation if it can be deleted by the current user and exists
        :param request: The HTTP POST request
        """
        if "pk" in request.POST and "machine_type" in request.POST:
            pk = request.POST.get("pk")
            machine_type = request.POST.get("machine_type")

            reservation = Reservation.get_reservation(machine_type, pk)

            if reservation and reservation.can_change(request.user):
                reservation.delete()

        return super().dispatch(request, *args, **kwargs)


class ChangeReservationView(ReservationCreateOrChangeView):
    """View for changing a reservation (Cannot be UpdateView due to the abstract inheritance of reservations)"""
    new_reservation = False

    def dispatch(self, request, *args, **kwargs):
        """
        Redirects the user to it's reservation page if the given reservation cannot be changed
        :param request: The HTTP request
        """
        # User must be able to change the given reservation
        if not kwargs["reservation"].can_change(request.user):
            return redirect("my_reservations")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form, **kwargs):
        """
        Handles updating the reservation if the form is valid, otherwise render the form view with an error code
        :param form: The valid form
        :return HTTP Response
        """
        reservation = kwargs["reservation"]
        # The user is not allowed to change the machine for a reservation
        if reservation.get_machine() != form.cleaned_data["machine"]:
            return redirect("my_reservations")

        reservation.start_time = form.cleaned_data["start_time"]
        reservation.end_time = form.cleaned_data["end_time"]
        if reservation.event:
            reservation.event = form.cleaned_data["event"]

        if reservation.special:
            reservation.special_text = form.cleaned_data["special_text"]

        return self.validate_and_save(reservation, form)
