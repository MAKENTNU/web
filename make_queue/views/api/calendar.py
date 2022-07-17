from django.http import JsonResponse
from django.utils.dateparse import parse_datetime
from django.views.generic import ListView

from users.models import User
from ..reservation.reservation import MachineRelatedViewMixin
from ...models.reservation import Reservation, ReservationRule


def reservation_type(reservation: Reservation, user: User):
    if reservation.special:
        return 'make'
    if reservation.event:
        return 'event'
    if user == reservation.user:
        return 'own'
    return 'normal'


class APIReservationListView(MachineRelatedViewMixin, ListView):
    model = Reservation

    def get_queryset(self):
        # TODO: use a form instead of manually parsing the URL parameters
        start_time = parse_datetime(self.request.GET.get('startDate'))
        end_time = parse_datetime(self.request.GET.get('endDate'))
        return self.machine.reservations.filter(start_time__lt=end_time, end_time__gt=start_time)

    def get_context_data(self, **kwargs):
        reservations = []
        for reservation in self.object_list:
            reservation_data = {
                'start': reservation.start_time,
                'end': reservation.end_time,
                'type': reservation_type(reservation, self.request.user),
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
            elif self.request.user.has_perm('make_queue.can_view_reservation_user'):
                reservation_data.update({
                    'user': reservation.user.get_full_name(),
                    'email': reservation.user.email,
                    'displayText': reservation.comment,
                })

            reservations.append(reservation_data)

        return {'reservations': reservations}

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
