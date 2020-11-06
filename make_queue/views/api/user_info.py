from django.http import HttpResponseNotFound, JsonResponse

from dataporten.ldap_utils import get_user_details_from_username


def get_user_info_from_username(request, username):
    details = get_user_details_from_username(username)
    return JsonResponse(details) if details else HttpResponseNotFound()
