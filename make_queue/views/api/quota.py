from abc import ABCMeta

from django.contrib.auth.models import User
from django.http import HttpResponse
from django.views import View

from dataporten.login_handlers import get_handler
from make_queue.models import Quota, Quota3D, QuotaSewing


def get_user_quota_max_length(request, machine_type):
    return HttpResponse(Quota.get_quota_by_machine(machine_type.literal, request.user).max_time_reservation)


class UpdateQuotaView(View):
    """Abstract class for an API method that updates a user quota"""
    __metaclass__ = ABCMeta

    def get_quota(self, username):
        """
        Retrieve the user quota of the quota_class specified in the subclass
        :param username: The username of the user
        :return: The user's quota
        """
        return self.quota_class.get_quota(User.objects.get(username=username))

    def post(self, request):
        """
        Update the quota with the specified fields on a post request
        :param request: The post request
        """
        quota = self.get_quota(request.POST.get("username"))
        for attribute_name, field_name, cast_function in self.fields:
            setattr(quota, attribute_name, cast_function(request.POST.get(field_name)))
        quota.save()
        return HttpResponse("Success")


class UpdateQuota3D(UpdateQuotaView):
    """API endpoint for changing a users 3D printing quota"""
    quota_class = Quota3D
    fields = (
        ("can_print", "can_print", lambda x: x == "true"),
        ("max_number_of_reservations", "max_number_of_reservations", float),
        ("max_time_reservation", "max_length_reservation", float),
    )


class UpdateSewingQuota(UpdateQuotaView):
    """API endpoint for changing a users sewing quota"""
    quota_class = QuotaSewing
    fields = (
        ("max_number_of_reservations", "max_number_of_reservations", float),
        ("max_time_reservation", "max_length_reservation", float),
    )


class UpdateAllowed(View):

    def post(self, request):
        if get_handler("printer_allowed").is_correct_token(request.POST.get("token", "")):
            get_handler("printer_allowed").update()
