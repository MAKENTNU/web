from django.views.generic import TemplateView

from make_queue.util.time import year_and_week_to_monday
from ...models.models import Machine, Quota


class ReservationCalendarView(TemplateView):
    """Main view for showing the reservation calendar for a machine"""
    template_name = "make_queue/reservation_overview.html"

    def get_context_data(self, year, week, machine):
        """
        Create the context required for the controls and the information to be displayed

        :param year: The year to show the calendar for
        :param week: The week to show the calendar for
        :param machine: The machine object to show the calendar for
        :return: context required to show the reservation calendar with controls
        """
        context = super().get_context_data()
        context.update({
            "can_create_reservations": False,
            "can_create_more_reservations": False,
            "can_ignore_rules": False,
            "other_machines": Machine.objects.exclude(pk=machine.pk).filter(machine_type=machine.machine_type).default_order_by(),
            "machine": machine,
            "year": year,
            "week": week,
            "date": year_and_week_to_monday(year, week),
        })

        if self.request.user.is_authenticated:
            context.update({
                "can_create_reservations": machine.machine_type.can_user_use(self.request.user),
                "can_create_more_reservations": Quota.can_make_new_reservation(self.request.user, machine.machine_type),
                "can_ignore_rules": any(
                    quota.can_create_more_reservations(self.request.user)
                    for quota in Quota.get_user_quotas(self.request.user, machine.machine_type).filter(ignore_rules=True)
                )
            })

        return context
