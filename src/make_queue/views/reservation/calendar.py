from django.views.generic import DetailView

from util.locale_utils import get_current_year_and_week, year_and_week_to_monday
from util.view_utils import QueryParameterFormMixin
from ...forms import MachineDetailQueryForm, ReservationListQueryForm
from ...models.machine import Machine
from ...models.reservation import Quota
from ...templatetags.reservation_extra import reservation_denied_message


class MachineDetailView(QueryParameterFormMixin, DetailView):
    """Main view for showing the reservation calendar for a machine."""
    model = Machine
    form_class = MachineDetailQueryForm
    template_name = 'make_queue/machine_detail.html'
    context_object_name = 'machine'
    extra_context = {
        'ReservationOwner': ReservationListQueryForm.Owner,
    }

    def get_queryset(self):
        return Machine.objects.visible_to(self.request.user)

    def get_context_data(self, **kwargs):
        """
        Create the context required for the controls and the information to be displayed.

        :return: context required to show the reservation calendar with controls
        """
        context = super().get_context_data(**kwargs)
        machine: Machine = self.object
        if self.request.GET:
            selected_year, selected_week = self.query_params['calendar_year'], self.query_params['calendar_week']
        else:
            selected_year, selected_week = get_current_year_and_week()

        context.update({
            'reservation_denied_message': reservation_denied_message(self.request.user, machine),
            'can_ignore_rules': False,
            'other_machines': (
                Machine.objects.exclude(pk=machine.pk).filter(
                    machine_type=machine.machine_type,
                ).visible_to(self.request.user).default_order_by()
            ),
            'selected_year': selected_year,
            'selected_week': selected_week,
            'selected_date': year_and_week_to_monday(selected_year, selected_week),
        })

        if self.request.user.is_authenticated:
            context.update({
                'can_ignore_rules': any(
                    quota.can_create_more_reservations(self.request.user)
                    for quota in Quota.get_user_quotas(self.request.user, machine.machine_type).filter(ignore_rules=True)
                )
            })

        return context
