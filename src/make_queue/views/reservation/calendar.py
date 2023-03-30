from django.http import HttpResponseRedirect
from django.views.generic import DetailView

from util.locale_utils import year_and_week_to_monday
from ...models.machine import Machine
from ...models.reservation import Quota
from ...templatetags.reservation_extra import current_calendar_url, reservation_denied_message


class MachineDetailView(DetailView):
    """Main view for showing the reservation calendar for a machine."""
    model = Machine
    template_name = 'make_queue/machine_detail.html'
    context_object_name = 'machine'

    redirect_to_current_week = False

    def get(self, request, *args, **kwargs):
        if self.redirect_to_current_week:
            return HttpResponseRedirect(current_calendar_url(self.get_object()))
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        return Machine.objects.visible_to(self.request.user)

    def get_context_data(self, **kwargs):
        """
        Create the context required for the controls and the information to be displayed.

        :return: context required to show the reservation calendar with controls
        """
        context = super().get_context_data(**kwargs)
        selected_year = self.kwargs['year']
        selected_week = self.kwargs['week']
        machine = self.object

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
