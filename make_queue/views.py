from django.views.generic.base import View
from django.views.generic import FormView
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.http.response import JsonResponse, HttpResponse
from django.contrib.auth.models import User
from datetime import datetime, timedelta
from make_queue.models import Machine, Reservation
from make_queue.forms import ReservationForm
from make_queue.templatetags.reservation_extra import calendar_url_reservation
from news.models import Event
import pytz


class ReservationCalendarView(View):
    template_name = "make_queue/reservation_calendar.html"

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
        return next(filter(lambda x: x.literal.lower() == machine_type.lower(), Machine.__subclasses__())).objects.all()

    @staticmethod
    def year_and_week_to_monday(year, week):
        return datetime.strptime(str(year) + " " + str(week) + " 1", "%Y %W %w")

    @staticmethod
    def date_to_percentage(date):
        date = timezone.localtime(date, timezone.get_default_timezone())
        return (date.hour / 24 + date.minute / 1440) * 100

    @staticmethod
    def format_reservation(reservation, date):
        start_time = max(reservation.start_time, date)
        end_time = min(reservation.end_time, date + timedelta(days=1, seconds=-1))

        return {'reservation': reservation,
                'start_percentage': ReservationCalendarView.date_to_percentage(start_time),
                'start_time': "{:02}:{:02}".format(start_time.hour, start_time.minute),
                'end_time': "{:02}:{:02}".format(end_time.hour, end_time.minute),
                'length': ReservationCalendarView.date_to_percentage(end_time) -
                          ReservationCalendarView.date_to_percentage(start_time)}

    def get(self, request, year="", week="", machine_type="", pk=""):
        year, week = int(year), int(week)

        if not self.is_valid_week(year, week):
            year, week = self.get_next_valid_week(year, week, 1)

        first_date_of_week = pytz.timezone(timezone.get_default_timezone_name()).localize(
            self.year_and_week_to_monday(year, week))

        machine = Machine.get_subclass(machine_type).objects.get(pk=pk)

        render_parameters = {'year': year, 'week': week, 'machine_type': machine_type, 'pk': pk,
                             'next': self.get_next_valid_week(year, week, 1),
                             'prev': self.get_next_valid_week(year, week, -1),
                             'machine_types': Machine.__subclasses__(),
                             'machine': machine}

        week_days = render_parameters['week_days'] = []
        for day_number in range(7):
            date = first_date_of_week + timedelta(days=day_number)
            week_days.append({
                "date": date,
                "machine": {"name": machine.name,
                            "machine": machine,
                            "reservations": list(map(lambda x: self.format_reservation(x, date),
                                                     machine.reservations_in_period(date, date + timedelta(days=1))))}

            })

        return render(request, self.template_name, render_parameters)


class MakeReservationView(FormView):
    template_name = "make_queue/make_reservation.html"

    def get(self, request, start_time="", selected_machine_type="", selected_machine_pk="-1", **kwargs):
        render_parameters = {"new_reservation": True, "start_time": start_time,
                             "selected_machine_type": selected_machine_type,
                             "selected_machine_pk": selected_machine_pk and int(selected_machine_pk) or -1,
                             "events": Event.objects.filter(
                                 Q(end_date=timezone.now().date(), end_time__gt=timezone.now().time()) |
                                 Q(end_date__gt=timezone.now().date())),
                             "machine_types": [
                                 {"literal": sub_class.literal, "instances": list(sub_class.objects.all())}
                                 for sub_class in Machine.__subclasses__()]}

        return render(request, self.template_name, render_parameters)

    def post(self, request, **kwargs):
        form = ReservationForm(request.POST)
        if not form.is_valid():
            # TODO: Implement redirect to form with parameters
            return

        reservation_type = Reservation.get_reservation_type(form.cleaned_data["machine_type"])

        reservation = reservation_type(start_time=form.cleaned_data["start_time"],
                                       end_time=form.cleaned_data["end_time"], user=request.user,
                                       machine=form.cleaned_data["machine"])

        if form.cleaned_data["event"]:
            reservation.event = form.cleaned_data["event"]

        if not reservation.validate():
            # TODO: Implement redirect to form with parameters
            return

        reservation.save()
        return redirect(calendar_url_reservation(reservation))


class MyReservationsView(View):
    template_name = "make_queue/my_reservations.html"

    @staticmethod
    def get_user_reservations(user):
        user_reservations = []
        for reservation_subclass in Reservation.__subclasses__():
            user_reservations.extend(reservation_subclass.objects.filter(user=user))
        return sorted(user_reservations, key=lambda x: x.end_time, reverse=True)

    def get(self, request):
        return render(request, self.template_name, {'reservations': self.get_user_reservations(request.user)})


class DeleteReservationView(View):

    def post(self, request):
        if "pk" in request.POST and "machine_type" in request.POST:
            pk = request.POST.get("pk")
            machine_type = request.POST.get("machine_type")

            reservation = Reservation.get_reservation(machine_type, pk)

            if reservation and reservation.user == request.user and reservation.can_delete():
                reservation.delete()
        return redirect("my_reservations")


class ChangeReservationView(View):
    template_name = "make_queue/make_reservation.html"

    def get(self, request, machine_type, pk):
        reservation = Reservation.get_reservation(machine_type, pk)
        if reservation is None or reservation.user != request.user:
            # TODO: Implement 404
            return None

        render_parameters = {"machine_types": [{"literal": machine_type, "instances": [reservation.get_machine()]}],
                             "selected_machine_type": machine_type, "selected_machine_pk": reservation.get_machine().pk,
                             "start_time": reservation.start_time, "end_time": reservation.end_time,
                             "event": reservation.event,
                             "events": Event.objects.filter(
                                 Q(end_date=timezone.now().date(), end_time__gt=timezone.now().time()) |
                                 Q(end_date__gt=timezone.now().date())),
                             "new_reservation": False}

        return render(request, self.template_name, render_parameters)

    def post(self, request, machine_type, pk):
        reservation = Reservation.get_reservation(machine_type, pk)
        if reservation is None or reservation.user != request.user or reservation.start_time < timezone.now():
            # TODO: Implement redirect
            return

        form = ReservationForm(request.POST)

        if not form.is_valid():
            # TODO: Implement redirect to form with parameters
            return

        if reservation.get_machine() != form.cleaned_data["machine"]:
            # TODO: Implement redirect
            return

        reservation.start_time = form.cleaned_data["start_time"]
        reservation.end_time = form.cleaned_data["end_time"]
        if reservation.event:
            reservation.event = form.cleaned_data["event"]

        if not reservation.validate():
            # TODO: Implement redirect
            return

        reservation.save()

        return redirect(calendar_url_reservation(reservation))


def get_reservations_day_and_machine(request, machine_type, pk, date):
    date = datetime.strptime(date, "%Y/%m/%d")
    reservations = Reservation.get_reservation_type(machine_type).objects.filter(machine__pk=pk,
                                                                                 start_time__lt=date + timedelta(
                                                                                     days=1)).filter(end_time__gte=date)
    data = {
        "reservations": reservations,
        "date": date
    }
    return JsonResponse(data)


def get_future_reservations_machine(request, machine_type, pk):
    reservations = Reservation.get_reservation_type(machine_type).objects.filter(machine__pk=pk,
                                                                                 end_time__gte=timezone.now())
    return JsonResponse(format_reservations_for_start_end_json(reservations))


def format_reservations_for_start_end_json(reservations):
    return {
        "reservations": [{"start_date": reservation.start_time, "end_date": reservation.end_time} for reservation in
                         reservations]
    }


def get_future_reservations_machine_without_specific_reservation(request, machine_type, pk, reservation_pk):
    reservations = Reservation.get_reservation_type(machine_type).objects.filter(
        machine__pk=pk, end_time__gte=timezone.now()).exclude(pk=reservation_pk)

    return JsonResponse(format_reservations_for_start_end_json(reservations))


class MachineView(View):
    template_name = "make_queue/reservation_machines.html"

    def get(self, request):
        render_parameters = {'machine_types': [
            {
                'name': machine_type.literal,
                'machines': [machine for machine in machine_type.objects.all()]
            } for machine_type in Machine.__subclasses__() if machine_type.objects.exists()
        ]}

        print(render_parameters)

        return render(request, self.template_name, render_parameters)


class QuotaView(View):
    template_name = "make_queue/quota_panel.html"

    def get(self, request):
        return render(request, self.template_name, {"users": User.objects.all(), "user": request.user})


def get_user_quota_view(request, username):
    user = get_object_or_404(User, username=username)
    return render(request, "make_queue/quota/quota_user.html", {"user": user})


class UpdateQuota3D(View):

    def post(self, request):
        print(request.user)
        print(request.POST["username"])
        return HttpResponse("")


class UpdateSewingQuota(View):

    def post(self, request):
        return HttpResponse("")
