from django.http import JsonResponse
from django.views.generic import ListView

from users.models import User
from util.locale_utils import iso_datetime_format
from util.view_utils import QueryParameterFormMixin
from ..reservation.reservation import MachineRelatedViewMixin
from ...forms import APIReservationListQueryForm
from ...models.reservation import Reservation, ReservationRule


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
        return JsonResponse(context)


class APIReservationRuleListView(MachineRelatedViewMixin, ListView):
    model = ReservationRule

    def get_queryset(self):
        return self.machine.machine_type.reservation_rules.all()

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
        return JsonResponse(context)
