from django.contrib.auth.models import User
from django.http import HttpResponse
from django.shortcuts import redirect
from django.views import View

from dataporten.login_handlers import get_handler
from make_queue.models import Quota


def get_user_quota_max_length(request, machine_type):
    return HttpResponse(Quota.get_quota_by_machine(machine_type.literal, request.user).max_time_reservation)


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
        return HttpResponse()


class UpdateSewingQuota(View):

    def post(self, request):
        user = User.objects.get(username=request.POST.get("username"))
        quota = user.quotasewing
        quota.max_number_of_reservations = request.POST.get("max_number_of_reservations")
        quota.max_time_reservation = request.POST.get("max_length_reservation")
        quota.save()
        return HttpResponse()


class UpdateAllowed(View):

    def post(self, request):
        if get_handler("printer_allowed").is_correct_token(request.POST.get("token", "")):
            update_printer_handler(request)
