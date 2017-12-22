from django.views.generic.base import View
from django.views.generic import FormView
from django.shortcuts import render
from django.utils.timezone import get_default_timezone_name
from datetime import datetime, timedelta
from make_queue.models import Printer3D, SewingMachine, Machine
from make_queue.forms import ReservationForm
import pytz


class ReservationCalendarView(View):
    template_name = "make_queue/reservation_calendar.html"

    @staticmethod
    def is_valid_week(year, week):
        first_day_of_week = datetime.strptime(str(year) + " " + str(week) + " 0", "%Y %W %w")
        return first_day_of_week.year == year

    @staticmethod
    def get_next_week(year, week):
        year, week = int(year) + (week == 52), (int(week) + 1) % 53
        if ReservationCalendarView.is_valid_week(year, week):
            return year, week
        return ReservationCalendarView.get_next_week(year, week)

    @staticmethod
    def get_prev_week(year, week):
        year, week = year - (week == 0), (week - 1) % 53
        if ReservationCalendarView.is_valid_week(year, week):
            return year, week
        return ReservationCalendarView.get_prev_week(year, week)

    @staticmethod
    def get_machines(machine_type):
        if machine_type.lower() in ["3d-printer", "3dprinter", "3d_printer"]:
            return list(Printer3D.objects.all())
        if machine_type.lower() in ["sewing", "sewing_machine"]:
            return list(SewingMachine.objects.all())
        raise ValueError("Cannot find the specific type")

    @staticmethod
    def format_reservation(reservation, date):
        reservation_json = {'reservation': reservation}

        if reservation.start_time < date:
            reservation_json['start_percentage'] = 0
            reservation_json['start_time'] = "00:00"
        else:
            reservation_json['start_percentage'] = (reservation.start_time.hour / 24 + reservation.start_time.minute / 1440)*100
            reservation_json['start_time'] = "{:2}:{:2}".format(reservation.start_time.hour, reservation.start_time.minute)

        if reservation.end_time >= date + timedelta(days=1):
            reservation_json['length'] = 100 - reservation_json['start_percentage']
            reservation_json['end_time'] = "23:59"
        else:
            reservation_json['length'] = (reservation.end_time.hour / 24 + reservation.end_time.minute / 1440)*100 - reservation_json['start_percentage']
            reservation_json['end_time'] = "{:2}:{:2}".format(reservation.end_time.hour, reservation.end_time.minute)

        return reservation_json

    def get(self, request, year="", week="", machine_type=""):
        year, week = map(int, [year, week])
        render_parameters = {'year': year, 'week': week, 'machine_type': machine_type}

        first_date_of_week = pytz.timezone(get_default_timezone_name()).localize(
            datetime.strptime(str(year) + " " + str(week) + " 1", "%Y %W %w"))

        if first_date_of_week.year != year:
            return self.get(request, *self.get_next_week(year, week), machine_type=machine_type)

        machines = self.get_machines(machine_type)
        render_parameters['machines'] = machines

        week_days = []
        for day_number in range(7):
            day = {}
            date = first_date_of_week + timedelta(days=day_number)
            day["date"] = date
            day["machines"] = []
            for machine in machines:
                day["machines"].append(
                    {"name": machine.name, "machine": machine, "reservations": list(
                        map(lambda x: self.format_reservation(x, date),
                            machine.reservations_in_period(date, date + timedelta(days=1))))})
            week_days.append(day)

        render_parameters['week_days'] = week_days

        render_parameters['next'] = self.get_next_week(year, week)
        render_parameters['prev'] = self.get_prev_week(year, week)
        return render(request, self.template_name, render_parameters)


class MakeReservationView(FormView):
    template_name = "make_queue/make_reservation.html"

    def get(self, request, start_time="", selected_machine_type="", selected_machine_pk="-1", **kwargs):
        render_parameters = {"form": ReservationForm(), "machine_types": [
            {"literal": sub_class.literal, "instances": list(sub_class.objects.all())}
            for sub_class in Machine.__subclasses__()
        ], "start_time": start_time, "selected_machine_type": selected_machine_type,
                             "selected_machine_pk": selected_machine_pk and int(selected_machine_pk) or -1}

        return render(request, self.template_name, render_parameters)
