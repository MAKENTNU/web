from http import HTTPStatus

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.generic import DeleteView, ListView, TemplateView, UpdateView

from users.models import User
from util.locale_utils import iso_datetime_format
from util.view_utils import PreventGetRequestsMixin, QueryParameterFormMixin, UTF8JsonResponse
from .forms import APIMachineDataQueryForm, APIReservationListQueryForm
from ..models.reservation import Quota, Reservation, ReservationRule
from ..templatetags.reservation_extra import can_delete_reservation, can_mark_reservation_finished
from ..views.machine import MachineRelatedViewMixin, MachineTypeRelatedViewMixin


class APIMachineDataView(LoginRequiredMixin, MachineRelatedViewMixin, QueryParameterFormMixin, TemplateView):
    form_class = APIMachineDataQueryForm

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['exclude_reservation'].queryset = self.machine.reservations
        return form

    def get_context_data(self, **kwargs):
        exclude_reservation = self.query_params['exclude_reservation']
        exclude_reservation_pk = exclude_reservation.pk if exclude_reservation else None
        return {
            'reservations': [
                {
                    'start_time': iso_datetime_format(r.start_time),
                    'end_time': iso_datetime_format(r.end_time),
                } for r in self.machine.reservations.filter(end_time__gte=timezone.now()).exclude(pk=exclude_reservation_pk)
            ],
            'can_ignore_rules': any(
                quota.can_create_more_reservations(self.request.user)
                for quota in Quota.get_user_quotas(self.request.user, self.machine.machine_type).filter(ignore_rules=True)
            ),
            'rules': [
                {
                    'periods': rule.get_exact_start_and_end_times_list(iso=False, wrap_using_modulo=True),
                    'max_hours': rule.max_hours,
                    'max_hours_crossed': rule.max_inside_border_crossed,
                } for rule in self.machine.machine_type.reservation_rules.all()],
        }

    def render_to_response(self, context, **response_kwargs):
        return UTF8JsonResponse(context)


class APIReservationRuleListView(MachineTypeRelatedViewMixin, ListView):
    model = ReservationRule

    def get_queryset(self):
        return self.machine_type.reservation_rules.all()

    def get_context_data(self, **kwargs):
        return {
            'rules': [
                {
                    'periods': rule.get_exact_start_and_end_times_list(iso=False, wrap_using_modulo=True),
                    'max_inside': rule.max_hours,
                    'max_crossed': rule.max_inside_border_crossed,
                } for rule in self.object_list
            ],
        }

    def render_to_response(self, context, **response_kwargs):
        return UTF8JsonResponse(context)


def reservation_type(reservation: Reservation, user: User):
    if reservation.special:
        return 'make'
    if reservation.event:
        return 'event'
    if user == reservation.user:
        return 'own'
    return 'normal'


class APIReservationListView(MachineRelatedViewMixin, QueryParameterFormMixin, ListView):
    model = Reservation
    form_class = APIReservationListQueryForm

    def get_queryset(self):
        start_time = self.query_params['start_date']
        end_time = self.query_params['end_date']
        return (self.machine.reservations.filter(start_time__lt=end_time, end_time__gt=start_time)
                .select_related('user').prefetch_related('event__event'))

    def get_context_data(self, **kwargs):
        return {'reservations': [
            self.build_reservation_dict(reservation, self.request.user)
            for reservation in self.object_list
        ]}

    @staticmethod
    def build_reservation_dict(reservation: Reservation, request_user: User) -> dict[str, str]:
        reservation_data = {
            'start': iso_datetime_format(reservation.start_time),
            'end': iso_datetime_format(reservation.end_time),
            'type': reservation_type(reservation, request_user),
        }

        if reservation.event:
            reservation_data.update({
                'eventLink': reservation.event.event.get_absolute_url(),
                'displayText': str(reservation.event.event.title),
            })
        elif reservation.special:
            reservation_data.update({
                'displayText': reservation.special_text,
            })
        elif request_user.has_perm('make_queue.can_view_reservation_user'):
            reservation_data.update({
                'user': reservation.user.get_full_name(),
                'email': reservation.user.email,
                'displayText': reservation.comment,
            })
        return reservation_data

    def render_to_response(self, context, **response_kwargs):
        return UTF8JsonResponse(context)


class APIReservationMarkFinishedView(PermissionRequiredMixin, PreventGetRequestsMixin, UpdateView):
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
            return UTF8JsonResponse({'message': message} if message else {}, status=HTTPStatus.BAD_REQUEST)

        reservation.end_time = timezone.localtime()
        reservation.save()
        return UTF8JsonResponse({}, status=HTTPStatus.OK)


class APIReservationDeleteView(PermissionRequiredMixin, PreventGetRequestsMixin, DeleteView):
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
            return UTF8JsonResponse({'message': message} if message else {}, status=HTTPStatus.BAD_REQUEST)

        reservation.delete()
        return UTF8JsonResponse({}, status=HTTPStatus.OK)
