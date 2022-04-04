from django.views.generic import DetailView

from util.locale_utils import year_and_week_to_monday
from ...models.machine import Machine
from ...models.reservation import Quota
from ...templatetags.reservation_extra import reservation_denied_message


class MachineDetailView(DetailView):
    """Main view for showing the reservation calendar for a machine."""
    model = Machine
    template_name = 'make_queue/machine_detail.html'
    context_object_name = 'machine'

    def get_context_data(self, **kwargs):
        """
        Create the context required for the controls and the information to be displayed.

        :return: context required to show the reservation calendar with controls
        """
        context = super().get_context_data(**kwargs)
        year = self.kwargs['year']
        week = self.kwargs['week']
        machine = self.object

        context.update({
            'reservation_denied_message': reservation_denied_message(self.request.user, machine),
            'can_ignore_rules': False,
            'other_machines': Machine.objects.exclude(pk=machine.pk).filter(machine_type=machine.machine_type).default_order_by(),
            'year': year,
            'week': week,
            'date': year_and_week_to_monday(year, week),
        })

        if self.request.user.is_authenticated:
            context.update({
                'can_ignore_rules': any(
                    quota.can_create_more_reservations(self.request.user)
                    for quota in Quota.get_user_quotas(self.request.user, machine.machine_type).filter(ignore_rules=True)
                )
            })

        return context
