from abc import ABC
from math import ceil

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.http import urlencode
from django.utils.translation import gettext_lazy as _, ngettext
from django.views.generic import FormView, ListView, TemplateView
from django_hosts import reverse

from news.models import TimePlace
from util.locale_utils import timedelta_to_hours
from util.logging_utils import log_request_exception
from util.view_utils import QueryParameterFormMixin
from .machine import MachineRelatedViewMixin
from ..forms.reservation import ReservationFindFreeSlotsForm, ReservationForm, ReservationListQueryForm
from ..models.machine import Machine, MachineType
from ..models.reservation import Reservation, ReservationRule
from ..templatetags.reservation_extra import calendar_url_reservation, can_change_reservation


# TODO: rewrite this whole view (and everything that uses it), so that it's more extendable,
#       and makes more use of the functionality of forms and Django's `CreateView` and `UpdateView`
class ReservationCreateOrUpdateView(TemplateView, ABC):
    """Base abstract class for the reservation create or change view."""
    template_name = 'make_queue/reservation_form.html'

    new_reservation: bool
    reservation: Reservation = None

    def get_error_message(self, form, reservation):
        """
        Generates the correct error message for the given form.

        :param reservation: The reservation to generate an error message for
        :param form: The form to generate an error message for
        :return: The error message
        """
        if not reservation.is_within_allowed_period() and not (reservation.special or reservation.event):
            num_days = reservation.FUTURE_LIMIT.days
            return ngettext(
                'Reservations can only be made {num_days} day ahead of time',
                'Reservations can only be made {num_days} days ahead of time',
                num_days
            ).format(num_days=num_days)
        if self.request.user.has_perm('make_queue.can_create_event_reservation') and form.cleaned_data["event"]:
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
            # Hack to "simulate" `ReservationUpdateView`
            self.reservation = reservation
            context_data = self.get_context_data()
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

        machine_queryset = Machine.objects.visible_to(self.request.user).default_order_by()
        # Always include a list of events and machines to populate the dropdown lists
        context_data = {
            "new_reservation": self.new_reservation,
            "event_timeplaces": list(TimePlace.objects.filter(end_time__gte=timezone.localtime())),
            "machine_types": [
                machine_type
                for machine_type in
                MachineType.objects.default_order_by().prefetch_machines(
                    machine_queryset=machine_queryset, machines_attr_name='instances',
                )
                if machine_type.can_user_use(self.request.user)
            ],
            "maximum_days_in_advance": Reservation.FUTURE_LIMIT.days,
        }

        # If we are updating an existing reservation, populate the information relevant to that reservation
        if not self.new_reservation or self.reservation:
            # noinspection PyUnresolvedReferences
            reservation = self.reservation  # Defined in `ReservationUpdateView`
            context_data["start_time"] = reservation.start_time
            context_data["reservation"] = reservation
            context_data["end_time"] = reservation.end_time
            context_data["selected_machine"] = reservation.machine
            context_data["event"] = reservation.event
            context_data["special"] = reservation.special
            context_data["special_text"] = reservation.special_text
            context_data["comment"] = reservation.comment
            context_data["can_change_start_time"] = reservation.can_change_start_time()
            context_data["can_change_end_time"] = reservation.can_change_end_time()
        # Otherwise populate with default information given to the view
        else:
            if hasattr(self, 'machine'):
                # Set in `ReservationCreateView`
                selected_machine = self.machine
            else:
                # `machine_pk` is only set in `test_get_context_data_non_reservation()` 🙃🔥
                selected_machine = get_object_or_404(Machine, pk=kwargs['machine_pk'])
            context_data["selected_machine"] = selected_machine
            if "start_time" in kwargs:
                context_data["start_time"] = kwargs["start_time"]
            context_data["can_change_start_time"] = True
            context_data["can_change_end_time"] = True

        return context_data

    def dispatch(self, request, *args, **kwargs):
        """
        If the request is a post request use the handle_post method,
        otherwise use the default method of the template view.

        :param request: The HTTP request
        :return: HTTP response
        """
        if request.method == 'POST':
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


class ReservationCreateView(PermissionRequiredMixin, MachineRelatedViewMixin, ReservationCreateOrUpdateView):
    """View for creating a new reservation."""
    new_reservation = True

    def has_permission(self):
        return self.machine.can_user_use(self.request.user)

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


class ReservationUpdateView(ReservationCreateOrUpdateView):
    """View for changing a reservation (Cannot be UpdateView due to the abstract inheritance of reservations)."""
    new_reservation = False
    reservation: Reservation

    @property
    def success_url(self):
        owner_param = urlencode({'owner': ReservationListQueryForm.Owner.ME})
        return f"{reverse('reservation_list')}?{owner_param}"

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        reservation_pk = self.kwargs['pk']
        self.reservation = get_object_or_404(Reservation, pk=reservation_pk)

    def dispatch(self, request, *args, **kwargs):
        """
        Redirects the user to its reservation page if the given reservation cannot be changed.

        :param request: The HTTP request
        """
        reservation = self.reservation
        # User must be able to change the given reservation
        if can_change_reservation(reservation, request.user):
            return super().dispatch(request, *args, **kwargs)
        else:
            return HttpResponseRedirect(self.success_url)

    def form_valid(self, form, **kwargs):
        """
        Handles updating the reservation if the form is valid, otherwise render the form view with an error code.

        :param form: The valid form
        :return: HTTP Response
        """
        reservation = self.reservation
        # The user is not allowed to change the machine for a reservation
        if reservation.machine != form.cleaned_data["machine"]:
            return HttpResponseRedirect(self.success_url)

        # If the reservation has begun, the user is not allowed to change the start time
        if reservation.start_time < timezone.now() and reservation.start_time != form.cleaned_data["start_time"]:
            return HttpResponseRedirect(self.success_url)

        reservation.comment = form.cleaned_data["comment"]

        reservation.start_time = form.cleaned_data["start_time"]
        reservation.end_time = form.cleaned_data["end_time"]
        if reservation.event:
            reservation.event = form.cleaned_data["event"]

        if reservation.special:
            reservation.special_text = form.cleaned_data["special_text"]

        return self.validate_and_save(reservation, form)


class ReservationListView(PermissionRequiredMixin, QueryParameterFormMixin, ListView):
    """View for listing either the user's reservations or MAKE's."""
    model = Reservation
    form_class = ReservationListQueryForm
    template_name = 'make_queue/reservation_list.html'
    context_object_name = 'reservations'
    extra_context = {
        'ReservationOwner': ReservationListQueryForm.Owner,
    }

    def has_permission(self):
        self.validate_query_params()
        if self._query_param_errors:
            return self.form_invalid()

        match self.query_params['owner']:
            case ReservationListQueryForm.Owner.ME:
                return self.request.user.is_authenticated
            case ReservationListQueryForm.Owner.MAKE:
                return self.user_has_admin_perms()

    def user_has_admin_perms(self):
        return self.request.user.has_perm('make_queue.can_create_event_reservation')

    def get_queryset(self):
        non_admin_reservations_query = Q(event=None, special=False)

        match self.query_params['owner']:
            case ReservationListQueryForm.Owner.ME:
                filter_query = Q(user=self.request.user)
                if not self.user_has_admin_perms():
                    filter_query &= non_admin_reservations_query
                queryset = Reservation.objects.filter(filter_query)

            case ReservationListQueryForm.Owner.MAKE:
                queryset = Reservation.objects.exclude(non_admin_reservations_query)

        # noinspection PyUnboundLocalVariable
        return queryset.order_by('-end_time', '-start_time')

    def get_context_data(self, **kwargs):
        return super().get_context_data(**{
            'reservations_owned_by_MAKE': self.query_params['owner'] == ReservationListQueryForm.Owner.MAKE,
            'has_admin_perms': self.user_has_admin_perms(),
            **kwargs,
        })


class ReservationFindFreeSlotsView(LoginRequiredMixin, FormView):
    """
    View to find free time slots for reservations.
    """
    form_class = ReservationFindFreeSlotsForm
    template_name = 'make_queue/reservation_find_free_slots.html'

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
                timezone.now() + Reservation.FUTURE_LIMIT
            ))
        # If the machine is not reserved anytime in the future, we include the
        # whole allowed period
        else:
            periods.append(self.format_period(
                machine,
                timezone.now(),
                timezone.now() + Reservation.FUTURE_LIMIT
            ))
        return periods

    def form_valid(self, form):
        """
        Renders the page with free slots in respect to the valid form.

        :param form: A valid ``ReservationFindFreeSlotsForm`` form
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
