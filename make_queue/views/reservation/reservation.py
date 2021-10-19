from abc import ABC
from datetime import timedelta
from math import ceil

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _, ngettext
from django.views.generic import DeleteView, FormView, TemplateView, UpdateView

from news.models import TimePlace
from util.locale_utils import timedelta_to_hours
from util.logging_utils import log_request_exception
from util.view_utils import PreventGetRequestsMixin
from ...forms import FreeSlotForm, ReservationForm
from ...models.models import Machine, MachineType, Reservation, ReservationRule
from ...templatetags.reservation_extra import calendar_url_reservation, can_delete_reservation, can_mark_reservation_finished


class ReservationCreateOrChangeView(TemplateView, ABC):
    """Base abstract class for the reservation create or change view."""

    template_name = 'make_queue/reservation_edit.html'

    def get_error_message(self, form, reservation):
        """
        Generates the correct error message for the given form.

        :param reservation: The reservation to generate an error message for
        :param form: The form to generate an error message for
        :return: The error message
        """
        if not reservation.is_within_allowed_period() and not (reservation.special or reservation.event):
            num_days = reservation.RESERVATION_FUTURE_LIMIT_DAYS
            return ngettext(
                'Reservations can only be made {num_days} day ahead of time',
                'Reservations can only be made {num_days} days ahead of time',
                num_days
            ).format(num_days=num_days)
        if self.request.user.has_perm("make_queue.can_create_event_reservation") and form.cleaned_data["event"]:
            return _("The time slot or event is no longer available")
        if reservation.check_machine_out_of_order():
            return _("The machine is out of order")
        if reservation.check_machine_maintenance():
            return _("The machine is under maintenance")
        if reservation.start_time == reservation.end_time:
            return _("The reservation cannot start and end at the same time")
        if not ReservationRule.covered_rules(reservation.start_time, reservation.end_time,
                                             reservation.machine.machine_type):
            return _("It is not possible to reserve the machine during these hours. Check the rules for when the machine is reservable")
        if not reservation.quota_can_create_reservation():
            return _("The reservation exceeds your quota")
        if reservation.check_start_time_after_end_time():
            return _("The start time can't be after the end time")
        if reservation.starts_before_now():
            return _("The reservation can't start in the past")
        return _("The time slot is not available")

    def validate_and_save(self, reservation, form):
        """
        Tries to validate and save the given reservation.

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
        Creates the context data required for the make reservation template.
        If reservation is given as a keyword argument, the view is made for that reservation.

        :param kwargs: The request arguments for creating the context data
        :return: The context data needed for the template
        """

        # Always include a list of events and machines to populate the dropdown lists
        context_data = {
            "new_reservation": self.new_reservation,
            "event_timeplaces": list(TimePlace.objects.filter(end_time__gte=timezone.localtime())),
            "machine_types": [
                machine_type
                for machine_type in
                MachineType.objects.prefetch_machines_and_default_order_by(machines_attr_name="instances")
                if machine_type.can_user_use(self.request.user)
            ],
            "maximum_days_in_advance": Reservation.RESERVATION_FUTURE_LIMIT_DAYS,
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
        If the request is a post request use the handle_post method,
        otherwise use the default method of the template view.

        :param request: The HTTP request
        :return: HTTP response
        """
        if request.method == "POST":
            return self.handle_post(request, **kwargs)
        return super().dispatch(request, *args, **kwargs)

    def handle_post(self, request, **kwargs):
        """
        Handles and validates update requests.

        :param request: The HTTP request
        """
        try:
            form = ReservationForm(request.POST)
            if form.is_valid():
                return self.form_valid(form, **kwargs)
        except Exception as e:
            log_request_exception("Validating reservation failed.", e, request)
        return self.get(request, **kwargs)


class CreateReservationView(PermissionRequiredMixin, ReservationCreateOrChangeView):
    """View for creating a new reservation."""
    new_reservation = True

    def has_permission(self):
        return self.kwargs['machine'].can_user_use(self.request.user)

    def form_valid(self, form, **kwargs):
        """
        Creates a reservation from a valid ``ReservationForm``.

        :param form: The valid reservation form
        :return: HTTP response
        """
        reservation = Reservation(
            start_time=form.cleaned_data["start_time"],
            end_time=form.cleaned_data["end_time"],
            user=self.request.user,
            machine=form.cleaned_data["machine"],
            comment=form.cleaned_data["comment"],
        )

        if form.cleaned_data["event"]:
            reservation.event = form.cleaned_data["event"]

        if form.cleaned_data["special"]:
            reservation.special = True
            reservation.special_text = form.cleaned_data["special_text"]

        return self.validate_and_save(reservation, form)


class DeleteReservationView(PermissionRequiredMixin, PreventGetRequestsMixin, DeleteView):
    model = Reservation

    def has_permission(self):
        user = self.request.user
        return (user.has_perm('make_queue.delete_reservation')
                or user == self.get_object().user)

    def delete(self, request, *args, **kwargs):
        reservation = self.get_object()
        if not can_delete_reservation(reservation, self.request.user):
            now = timezone.now()
            if reservation.start_time <= now:
                if reservation.end_time > now:
                    message = _("Cannot delete reservation when it has already started. Mark it as finished instead.")
                else:
                    message = _("Cannot delete reservation when it has already ended.")
            else:
                message = None
            return JsonResponse({'message': message} if message else {}, status=400)

        reservation.delete()
        return HttpResponse(status=200)


class ChangeReservationView(ReservationCreateOrChangeView):
    """View for changing a reservation (Cannot be UpdateView due to the abstract inheritance of reservations)."""
    new_reservation = False

    def dispatch(self, request, *args, **kwargs):
        """
        Redirects the user to its reservation page if the given reservation cannot be changed.

        :param request: The HTTP request
        """
        # User must be able to change the given reservation
        reservation = kwargs["reservation"]
        if reservation.can_change(request.user) or reservation.can_change_end_time(request.user):
            return super().dispatch(request, *args, **kwargs)
        else:
            return redirect("my_reservations")

    def form_valid(self, form, **kwargs):
        """
        Handles updating the reservation if the form is valid, otherwise render the form view with an error code.

        :param form: The valid form
        :return: HTTP Response
        """
        reservation = kwargs["reservation"]
        # The user is not allowed to change the machine for a reservation
        if reservation.machine != form.cleaned_data["machine"]:
            return redirect("my_reservations")

        # If the reservation has begun, the user is not allowed to change the start time
        if reservation.start_time < timezone.now() and reservation.start_time != form.cleaned_data["start_time"]:
            return redirect("my_reservations")

        reservation.comment = form.cleaned_data["comment"]

        reservation.start_time = form.cleaned_data["start_time"]
        reservation.end_time = form.cleaned_data["end_time"]
        if reservation.event:
            reservation.event = form.cleaned_data["event"]

        if reservation.special:
            reservation.special_text = form.cleaned_data["special_text"]

        return self.validate_and_save(reservation, form)


class MarkReservationFinishedView(PermissionRequiredMixin, PreventGetRequestsMixin, UpdateView):
    model = Reservation

    def has_permission(self):
        user = self.request.user
        return (user.has_perm('make_queue.change_reservation')
                or user == self.get_object().user)

    def post(self, request, *args, **kwargs):
        reservation = self.get_object()
        if not can_mark_reservation_finished(reservation):
            now = timezone.now()
            if reservation.start_time > now:
                message = _("Cannot mark reservation as finished when it has not started yet.")
            elif reservation.end_time <= now:
                message = _("Cannot mark reservation as finished when it has already ended.")
            else:
                message = None
            return JsonResponse({'message': message} if message else {}, status=400)

        reservation.end_time = timezone.localtime()
        reservation.save()
        return HttpResponse(status=200)


class FindFreeSlot(FormView):
    """
    View to find free time slots for reservations.
    """
    form_class = FreeSlotForm
    template_name = 'make_queue/find_free_slot.html'

    def get_initial(self):
        return {'machine_type': MachineType.objects.first()}

    @staticmethod
    def format_period(machine, start_time, end_time):
        """
        Formats a time period for the context.
        """
        return {
            'machine': machine,
            'start_time': start_time,
            'end_time': end_time,
            'duration': ceil(timedelta_to_hours(end_time - start_time)),
        }

    def get_periods(self, machine: Machine, required_time):
        """
        Finds all future periods for the given machine with a minimum length.

        :param machine: The machine to get periods for
        :param required_time: The minimum required time for the period
        :return: A list of periods
        """
        periods = []
        reservations = list(
            machine.reservations.filter(end_time__gte=timezone.now()).order_by('start_time')
        )

        # Find all periods between reservations
        for period_start, period_end in zip(reservations, reservations[1:]):
            duration = timedelta_to_hours(
                period_end.start_time - period_start.end_time)
            if duration >= required_time:
                periods.append(self.format_period(
                    machine,
                    period_start.end_time,
                    period_end.start_time
                ))

        # Add remaining time after last reservation
        if reservations:
            periods.append(self.format_period(
                machine, reservations[-1].end_time,
                timezone.now() + timedelta(days=Reservation.RESERVATION_FUTURE_LIMIT_DAYS)
            ))
        # If the machine is not reserved anytime in the future, we include the
        # whole allowed period
        else:
            periods.append(self.format_period(
                machine,
                timezone.now(),
                timezone.now() + timedelta(days=Reservation.RESERVATION_FUTURE_LIMIT_DAYS)
            ))
        return periods

    def form_valid(self, form):
        """
        Renders the page with free slots in respect to the valid form.

        :param form: A valid FreeSlotForm form
        :return: A HTTP response rendering the page with the found free slots
        """
        context = self.get_context_data()

        # Time should be expressed in hours
        required_time = form.cleaned_data['hours'] + form.cleaned_data['minutes'] / 60

        periods = []
        for machine in form.cleaned_data['machine_type'].machines.all():
            if not machine.get_status() == Machine.Status.OUT_OF_ORDER:
                periods.extend(self.get_periods(machine, required_time))

        # Periods in the near future is more interesting than in the distant
        # future
        periods.sort(key=lambda period: period['start_time'])

        context.update({
            'free_slots': periods,
        })
        return self.render_to_response(context)
