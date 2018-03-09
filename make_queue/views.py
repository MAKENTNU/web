from django.views.generic.base import View
from django.views.generic import FormView
from django.db.models import Q
from django.shortcuts import render, redirect
from django.utils import timezone
from django.http.response import JsonResponse, HttpResponse, HttpResponseRedirect
from django.contrib.auth.models import User
from datetime import datetime, timedelta
from .helper import date_to_local, local_to_date
from .models import Machine, Reservation, Quota
from .forms import ReservationForm
from .templatetags.reservation_extra import calendar_url_reservation, date_to_percentage
from news.models import TimePlace
from dataporten.login_handlers import get_handler


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


class AdminReservationView(View):
    template_name = "make_queue/reservations.html"

    def get(self, request):
        event_reservation = []
        for reservation_subclass in Reservation.__subclasses__():
            event_reservation.extend(reservation_subclass.objects.exclude(event=None, special=False))
        return render(request, self.template_name, {"reservations": event_reservation, "admin": True})


class MakeReservationView(FormView):
    template_name = "make_queue/make_reservation.html"

    @staticmethod
    def build_parameters(machine, user, start_time="", end_time="", event=""):
        return {"new_reservation": True, "start_time": start_time, "end_time": end_time, "selected_machine": machine,
                "quota": Quota.get_quota_by_machine(machine.literal, user), "event": event,
                "events": TimePlace.objects.filter(
                    Q(end_date=timezone.now().date(), end_time__gt=timezone.now().time()) |
                    Q(end_date__gt=timezone.now().date())),
                "machine_types": [
                    {"literal": sub_class.literal, "instances": list(sub_class.objects.all())}
                    for sub_class in Machine.__subclasses__() if
                    Quota.get_quota_by_machine(sub_class.literal, user).can_make_new_reservation()]}

    def get(self, request, machine, start_time="", **kwargs):
        render_parameters = self.build_parameters(machine, request.user, start_time=start_time)
        return render(request, self.template_name, render_parameters)

    def post(self, request, **kwargs):
        try:
            form = ReservationForm(request.POST)
            if not form.is_valid():
                # Go to the make reservation page, if the reservation is not valid
                return self.get(request, **kwargs)
        except Exception:
            # Go to the make reservation page, if the reservation is not valid
            return self.get(request, **kwargs)

        reservation_type = Reservation.get_reservation_type(form.cleaned_data["machine_type"])

        reservation = reservation_type(start_time=form.cleaned_data["start_time"],
                                       end_time=form.cleaned_data["end_time"], user=request.user,
                                       machine=form.cleaned_data["machine"])

        if form.cleaned_data["event"]:
            reservation.event = form.cleaned_data["event"]

        if form.cleaned_data["special"]:
            reservation.special = True
            reservation.special_text = form.cleaned_data["special_text"]

        if not reservation.validate():
            render_parameters = self.build_parameters(form.cleaned_data["machine"], request.user,
                                                      start_time=form.cleaned_data["start_time"],
                                                      end_time=form.cleaned_data["end_time"],
                                                      event=form.cleaned_data["event"] if form.cleaned_data[
                                                          "event"] else "")
            # The errors may be the time being taken or if the user can make event reservations and this
            # is an event reservation the event being deleted
            render_parameters["error"] = "Tidspunktet" + " eller eventen," * (request.user.has_perm(
                "can_create_event_reservation") * (not (
                not form.cleaned_data["event"]))) + " er ikke lengre tilgjengelig"
            return render(request, self.template_name, render_parameters)

        reservation.save()
        return redirect(calendar_url_reservation(reservation))


class MyReservationsView(View):
    template_name = "make_queue/reservations.html"

    @staticmethod
    def get_user_reservations(user):
        user_reservations = []
        for reservation_subclass in Reservation.__subclasses__():
            user_reservations.extend(reservation_subclass.objects.filter(user=user, event=None, special=False))
        return sorted(user_reservations, key=lambda x: x.end_time, reverse=True)

    def get(self, request):
        return render(request, self.template_name, {'reservations': self.get_user_reservations(request.user)})


class DeleteReservationView(View):

    def post(self, request):
        if "pk" in request.POST and "machine_type" in request.POST:
            pk = request.POST.get("pk")
            machine_type = request.POST.get("machine_type")

            reservation = Reservation.get_reservation(machine_type, pk)

            if reservation and reservation.can_change(request.user):
                reservation.delete()
        if "next" in request.POST:
            return HttpResponseRedirect(request.POST.get("next"))
        return redirect("my_reservations")


class ChangeReservationView(View):
    template_name = "make_queue/make_reservation.html"

    @staticmethod
    def build_parameters(reservation):
        return {"machine_types": [{"literal": reservation.get_machine().literal,
                                   "instances": [reservation.get_machine()]}], "new_reservation": False,
                "quota": reservation.get_quota(), "selected_machine": reservation.get_machine(),
                "event": reservation.event, "start_time": reservation.start_time, "end_time": reservation.end_time,
                "special": reservation.special, "special_text": reservation.special_text,
                "events": TimePlace.objects.filter(
                    Q(end_date=timezone.now().date(), end_time__gt=timezone.now().time()) |
                    Q(end_date__gt=timezone.now().date()))}

    def get(self, request, reservation):
        # Users should not be able to see the edit page for other users reservations or their own old reservations
        if not reservation.can_change(request.user):
            return redirect("my_reservations")

        return render(request, self.template_name, self.build_parameters(reservation))

    def post(self, request, reservation):
        # The reservation must be valid, for the same user as the one sending the request and not have started
        if reservation is None or not reservation.can_change(request.user):
            return redirect("my_reservations")

        try:
            form = ReservationForm(request.POST)
            if not form.is_valid():
                # Go back to the change reservation page if the form is missing fields or the fields have invalid value
                return self.get(request, reservation)
        except Exception:
            # Go back to the change reservation page if the form is missing fields or the fields have invalid values
            return self.get(request, reservation)

        # The user is not allowed to change the machine for a reservation
        if reservation.get_machine() != form.cleaned_data["machine"]:
            return redirect("my_reservations")

        reservation.start_time = form.cleaned_data["start_time"]
        reservation.end_time = form.cleaned_data["end_time"]
        if reservation.event:
            reservation.event = form.cleaned_data["event"]

        if reservation.special:
            reservation.special_text = form.cleaned_data["special_text"]

        if not reservation.validate():
            render_parameters = self.build_parameters(reservation)
            # The errors may be the time being taken or if the user can make event reservations and this
            # is an event reservation the event being deleted
            render_parameters["error"] = "Tidspunktet" + " eller eventen," * (request.user.has_perm(
                "can_create_event_reservation") * bool(not form.cleaned_data["event"])) + " er ikke lengre tilgjengelig"
            return render(request, self.template_name, render_parameters)

        reservation.save()

        return redirect(calendar_url_reservation(reservation))


def get_reservations_day_and_machine(request, machine, date):
    reservations = machine.get_reservation_set().filter(start_time__lt=date + timedelta(days=1)).filter(
        end_time__gte=date)

    data = {
        "reservations": reservations,
        "date": date
    }
    return JsonResponse(data)


def get_future_reservations_machine(request, machine):
    reservations = machine.get_reservation_set().filter(end_time__gte=timezone.now())
    return JsonResponse(format_reservations_for_start_end_json(reservations))


def format_reservations_for_start_end_json(reservations):
    return {
        "reservations": [{"start_date": reservation.start_time, "end_date": reservation.end_time} for reservation in
                         reservations]
    }


def get_user_quota_max_length(request, machine_type):
    return HttpResponse(Quota.get_quota_by_machine(machine_type.literal, request.user).max_time_reservation)


def get_future_reservations_machine_without_specific_reservation(request, reservation):
    reservations = reservation.machine.get_reservation_set().filter(end_time__gte=timezone.now()).exclude(
        pk=reservation.pk)

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

        return render(request, self.template_name, render_parameters)


class QuotaView(View):
    template_name = "make_queue/quota_panel.html"

    def get(self, request):
        return render(request, self.template_name, {"users": User.objects.all(), "user": request.user})


def get_user_quota_view(request, user):
    return render(request, "make_queue/quota/quota_user.html", {"user": user})


def update_printer_handler(request):
    get_handler("printer_allowed").update()
    return redirect("quota_panel")


class UpdateQuota3D(View):

    def post(self, request):
        user = User.objects.get(username=request.POST.get("username"))
        quota = user.quota3d
        quota.can_print = request.POST.get("can_print") == "true"
        quota.max_number_of_reservations = request.POST.get("max_number_of_reservations")
        quota.max_time_reservation = request.POST.get("max_length_reservation")
        quota.save()
        return HttpResponse("")


class UpdateSewingQuota(View):

    def post(self, request):
        user = User.objects.get(username=request.POST.get("username"))
        quota = user.quotasewing
        quota.max_number_of_reservations = request.POST.get("max_number_of_reservations")
        quota.max_time_reservation = request.POST.get("max_length_reservation")
        quota.save()
        return HttpResponse("")
