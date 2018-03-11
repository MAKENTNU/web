from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.utils import timezone
from django.views import View
from django.views.generic import FormView

from make_queue.forms import ReservationForm
from make_queue.models import Quota, Machine, Reservation
from make_queue.templatetags.reservation_extra import calendar_url_reservation
from news.models import TimePlace


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
