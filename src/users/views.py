from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import HttpResponseNotFound, JsonResponse
from django.views import View

from dataporten.ldap_utils import get_user_details_from_username


class AdminAPIBasicUserInfoView(PermissionRequiredMixin, View):
    permission_required = ('users.view_user',)

    def get(self, request, *args, **kwargs):
        username = kwargs['username']
        user_details = get_user_details_from_username(username)
        return JsonResponse(user_details) if user_details else HttpResponseNotFound()
