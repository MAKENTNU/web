from datetime import timedelta

from django.utils import timezone
from django.views.generic import TemplateView

from make_queue.models import Machine, Quota
from make_queue.templatetags.reservation_extra import date_to_percentage
from make_queue.util.time import is_valid_week, get_next_week, year_and_week_to_monday, local_to_date


class ReservationCalendarComponentView(TemplateView):
    """View for the reservation calendar and components that rely on it"""
    template_name = "make_queue/reservation_calendar.html"

    @staticmethod
    def format_reservation(reservation, date):
        """
        Creates a dictionary of reservation data for a given reservation. Formats the data to a given date so that the
        template can create a nicely formatted block in the calendar for the reservation

        :param reservation: The reservation to create formatted data for
        :param date: The date to format the data for
        :return: Formatted data for the given reservation
        """
        # If the start time is before the given date, set it to the start of the given date
        start_time = max(reservation.start_time, date)
        # If the end time is after the end of the given date, set it to the end of the given date
        end_time = min(reservation.end_time, date + timedelta(days=1, seconds=-1))

        return {'reservation': reservation, 'start_percentage': date_to_percentage(start_time),
                'start_time': "{:02}:{:02}".format(start_time.hour, start_time.minute),
                'end_time': "{:02}:{:02}".format(end_time.hour, end_time.minute),
                'length': date_to_percentage(end_time) - date_to_percentage(start_time)}

    @staticmethod
    def get_week_days_with_reservations(year, week, machine):
        """
        Creates a list of the week days with reservation for the given year, week and machine

        :param year: The year the week is in
        :param week: The week to retrieve reservations for
        :param machine: The machine to retrieve reservations for
        :return: A list of week days with reservations
        """
        first_date_of_week = local_to_date(year_and_week_to_monday(year, week))

        return [{
            "date": date,
            "reservations": list(map(lambda x: ReservationCalendarComponentView.format_reservation(x, date),
                                     machine.reservations_in_period(date, date + timedelta(days=1))))
        } for date in [first_date_of_week + timedelta(days=day_number) for day_number in range(7)]]

    def get_context_data(self, year, week, machine):
        """
        Create the context required for the given machine in the given week of the given year.
        The context also includes the year and week in case they changed.

        :param year: The year to show the calendar for
        :param week: The week to show the calendar for
        :param machine: The machine object to show the calendar for
        :return: context for the reservation calendar
        """
        if not is_valid_week(year, week):
            year, week = get_next_week(year, week, 1)

        return {'week_days': self.get_week_days_with_reservations(year, week, machine), "week": week, "year": year,
                "machine": machine, "now": timezone.now()}


class ReservationCalendarView(ReservationCalendarComponentView):
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
        context = super().get_context_data(year, week, machine)
        context["next"] = get_next_week(context["year"], context["week"], 1)
        context["prev"] = get_next_week(context["year"], context["week"], -1)
        context["machine_types"] = Machine.__subclasses__()

        if self.request.user.is_authenticated:
            context["can_make_more_reservations"] = Quota.get_quota_by_machine(machine.literal, self.request.user) \
                .can_make_new_reservation()

        return context
