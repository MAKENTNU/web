from abc import ABCMeta
from math import ceil

from django.db.models import Q
from django.shortcuts import render, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import RedirectView, TemplateView, FormView
from django.utils.translation import gettext_lazy as _

from make_queue.fields import MachineTypeField
from make_queue.forms import ReservationForm, FreeSlotForm
from make_queue.models.models import Machine, Reservation
from make_queue.templatetags.reservation_extra import calendar_url_reservation
from make_queue.util.time import timedelta_to_hours
from news.models import TimePlace


class ReservationCreateOrChangeView(TemplateView):
    """Base abstract class for the reservation create or change view"""
    __metaclass__ = ABCMeta
    template_name = "make_queue/make_reservation.html"

    def get_error_message(self, form, reservation):
        """
        Generates the correct error message for the given form
        :param reservation: The reservation to generate an error message for
        :param form: The form to generate an error message for
        :return: The error message
        """
        if not reservation.is_within_allowed_period_for_reservation() and not (
                reservation.special or reservation.event):
            """Translation: Reservasjoner kan bare lages {:} dager frem i tid"""
            return _("Reservations can only be made {:} days ahead of time".format(
                reservation.reservation_future_limit_days))
        if self.request.user.has_perm("make_queue.can_create_event_reservation") and form.cleaned_data["event"]:
            """Translation: Tidspunktet eller eventen, er ikke lengre tilgjengelig"""
            return _("The time slot or event, is no longer available")
        if not reservation.quota_can_make_reservation():
            """Translation: Reservasjonen går over kvoten"""
            return _("The reservation exceeds the quota")
        if reservation.check_start_time_after_end_time():
            """Translation: Starttiden kan ikke være etter sluttiden"""
            return _("The start time can't be after the end time")
        if reservation.reservation_starts_before_now():
            """Translation: Reservasjonen kan ikke starte i fortiden"""
            return _("The reservation can't start in the past")
        """Translation: Tidspunktet er ikke tilgjengelig"""
        return _("The time slot is not available")

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
            context_data["error"] = self.get_error_message(form, reservation)
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
                {"literal": machine_type.name, "instances": Machine.objects.filter(machine_type=machine_type)}
                for machine_type in MachineTypeField.possible_machine_types if
                machine_type.can_user_use(self.request.user)
            ],
            "maximum_days_in_advance": Reservation.reservation_future_limit_days
        }

        # If we are given a reservation, populate the information relevant to that reservation
        if "reservation" in kwargs:
            reservation = kwargs["reservation"]
            context_data["start_time"] = reservation.start_time
            context_data["reservation_pk"] = reservation.pk
            context_data["end_time"] = reservation.end_time
            context_data["selected_machine"] = reservation.machine
            context_data["event"] = reservation.event
            context_data["special"] = reservation.special
            context_data["special_text"] = reservation.special_text
            context_data["comment"] = reservation.comment
            context_data["can_change_start_time"] = reservation.can_change(self.request.user)
        # Otherwise populate with default information given to the view
        else:
            context_data["selected_machine"] = kwargs["machine"]
            if "start_time" in kwargs:
                context_data["start_time"] = kwargs["start_time"]
            context_data["can_change_start_time"] = True

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
        reservation = Reservation(start_time=form.cleaned_data["start_time"],
                                  end_time=form.cleaned_data["end_time"], user=self.request.user,
                                  machine=form.cleaned_data["machine"], comment=form.cleaned_data["comment"])

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
        if "pk" in request.POST:
            pk = request.POST.get("pk")

            try:
                reservation = Reservation.objects.get(pk=pk)
                if reservation.can_delete(request.user):
                    reservation.delete()
            except Reservation.DoesNotExist:
                pass

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
        if not kwargs["reservation"].can_change(request.user) and not kwargs["reservation"].can_change_end_time(
                request.user):
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
        if reservation.machine != form.cleaned_data["machine"]:
            return redirect("my_reservations")

        reservation.comment = form.cleaned_data["comment"]

        reservation.start_time = form.cleaned_data["start_time"]
        reservation.end_time = form.cleaned_data["end_time"]
        if reservation.event:
            reservation.event = form.cleaned_data["event"]

        if reservation.special:
            reservation.special_text = form.cleaned_data["special_text"]

        return self.validate_and_save(reservation, form)


class MarkReservationAsDone(RedirectView):
    url = reverse_lazy("my_reservations")

    def get_redirect_url(self, *args, next_url=None, **kwargs):
        if next_url is not None:
            return next_url
        return super().get_redirect_url(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        pk = request.POST.get("pk", default=0)
        reservations = Reservation.objects.filter(pk=pk)
        if not reservations.exists():
            return self.get(request, *args, **kwargs)

        reservation = reservations.first()
        if not reservation.can_change_end_time(request.user) or reservation.start_time >= timezone.now():
            return self.get(request, *args, **kwargs)

        reservation.end_time = timezone.now()
        reservation.save()

        return self.get(request, *args, **kwargs)


class FindFreeSlot(FormView):
    """
    View to find free time slots for reservations
    """
    template_name = "make_queue/find_free_slot.html"
    form_class = FreeSlotForm

    @staticmethod
    def format_period(machine, start_time, end_time):
        """
        Formats a time period for the context
        """
        return {
            "machine": machine,
            "start_time": start_time,
            "end_time": end_time,
            "duration": ceil(timedelta_to_hours(end_time - start_time))
        }

    def get_periods(self, machine, required_time):
        """
        Finds all future periods for the given machine with a minimum length

        :param machine: The machine to get periods for
        :param required_time: The minimum required time for the period
        :return: A list of periods
        """
        periods = []
        reservations = list(
            Reservation.objects.filter(end_time__gte=timezone.now(), machine__pk=machine.pk).order_by("start_time"))

        # Find all periods between reservations
        for period_start, period_end in zip(reservations, reservations[1:]):
            duration = timedelta_to_hours(period_end.start_time - period_start.end_time)
            if duration >= required_time:
                periods.append(self.format_period(machine, period_start.end_time, period_end.start_time))

        # Add remaining time after last reservation
        if reservations:
            periods.append(self.format_period(
                machine, reservations[-1].end_time,
                timezone.now() + timezone.timedelta(days=Reservation.reservation_future_limit_days)))
        # If the machine is not reserved anytime in the future, we include the whole allowed period
        else:
            periods.append(self.format_period(
                machine, timezone.now(),
                timezone.now() + timezone.timedelta(days=Reservation.reservation_future_limit_days)))
        return periods

    def form_valid(self, form):
        """
        Renders the page with free slots in respect to the valid form

        :param form: A valid FreeSlotForm form
        :return: A HTTP response rendering the page with the found free slots
        """
        context = self.get_context_data()

        # Time should be expressed in hours
        required_time = form.cleaned_data["hours"] + form.cleaned_data["minutes"] / 60

        periods = []
        for machine in Machine.objects.filter(machine_type=form.cleaned_data["machine_type"]):
            # Checks if the machine is not out-of-order
            if not machine.get_status() in "O":
                periods += self.get_periods(machine, required_time)

        # Periods in the near future is more interesting than in the distant future
        periods.sort(key=lambda period: period["start_time"])

        context.update({
            "free_slots": periods,
        })
        return self.render_to_response(context)
