from django.http import JsonResponse
from django.utils import timezone
from django.views.generic import TemplateView

from util.locale_utils import iso_datetime_format
from util.view_utils import QueryParameterFormMixin
from ..reservation.reservation import MachineRelatedViewMixin
from ...forms import APIMachineDataQueryForm
from ...models.reservation import Quota


class APIMachineDataView(MachineRelatedViewMixin, QueryParameterFormMixin, TemplateView):
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
        return JsonResponse(context)
