from datetime import timedelta

from django.shortcuts import render
from django.utils.datetime_safe import datetime
from django.views import View

from make_queue.helper import local_to_date
from make_queue.models import Machine, Quota
from make_queue.templatetags.reservation_extra import date_to_percentage


class ReservationCalendarView(View):
    template_name = "make_queue/reservation_overview.html"

    @staticmethod
    def is_valid_week(year, week):
        return week != 0 and ReservationCalendarView.year_and_week_to_monday(year, week).year == year

    @staticmethod
    def get_next_valid_week(year, week, shift_direction):
        year, week = year + ((week + shift_direction) // 54), (week + shift_direction) % 54
        if ReservationCalendarView.is_valid_week(year, week):
            return year, week
        return ReservationCalendarView.get_next_valid_week(year, week, shift_direction)

    @staticmethod
    def get_machines(machine_type):
        return Machine.get_subclass(machine_type).objects.all()

    @staticmethod
    def year_and_week_to_monday(year, week):
        return datetime.strptime(str(year) + " " + str(week) + " 1", "%Y %W %w")

    @staticmethod
    def format_reservation(reservation, date):
        start_time = max(reservation.start_time, date)
        end_time = min(reservation.end_time, date + timedelta(days=1, seconds=-1))

        return {'reservation': reservation, 'start_percentage': date_to_percentage(start_time),
                'start_time': "{:02}:{:02}".format(start_time.hour, start_time.minute),
                'end_time': "{:02}:{:02}".format(end_time.hour, end_time.minute),
                'length': date_to_percentage(end_time) - date_to_percentage(start_time)}

    @staticmethod
    def get_week_days_with_reservations(year, week, machine):
        first_date_of_week = local_to_date(ReservationCalendarView.year_and_week_to_monday(year, week))
        week_days = []
        for day_number in range(7):
            date = first_date_of_week + timedelta(days=day_number)
            week_days.append({
                "date": date,
                "machine": {"name": machine.name, "machine": machine,
                            "reservations": list(map(lambda x: ReservationCalendarView.format_reservation(x, date),
                                                     machine.reservations_in_period(date, date + timedelta(days=1))))}
            })

        return week_days

    def get(self, request, year, week, machine):
        if not self.is_valid_week(year, week):
            year, week = self.get_next_valid_week(year, week, 1)

        render_parameters = {'year': year, 'week': week, 'next': self.get_next_valid_week(year, week, 1),
                             'prev': self.get_next_valid_week(year, week, -1),
                             'machine_types': Machine.__subclasses__(),
                             'machine': machine, 'week_days': self.get_week_days_with_reservations(year, week, machine)}

        if request.user.is_authenticated:
            render_parameters["can_make_more_reservations"] = Quota.get_quota_by_machine(machine.literal, request.user) \
                .can_make_new_reservation()

        return render(request, self.template_name, render_parameters)


class ReservationCalendarComponentView(View):
    template_name = "make_queue/reservation_calendar.html"

    def get(self, request, machine, year, week):
        if not ReservationCalendarView.is_valid_week(year, week):
            year, week = ReservationCalendarView.get_next_valid_week(year, week, 1)

        return render(request, self.template_name,
                      {'week_days': ReservationCalendarView.get_week_days_with_reservations(year, week, machine)})
