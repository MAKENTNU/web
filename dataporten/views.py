from django.views import View
from django.http import HttpResponseRedirect
from django.contrib.auth import logout
from django.conf import settings
from social_django.views import complete

from dataporten.ldap_utils import get_user_details_from_email


class Logout(View):
    def get(self, request):
        logout(request)
        return HttpResponseRedirect(settings.LOGOUT_URL)


def login_wrapper(request, backend, *args, **kwargs):
    response = complete(request, backend, *args, **kwargs)
    user = request.user
    data = user.social_auth.first().extra_data

    # Update the full name of the user
    user.first_name = ' '.join(data['fullname'].split()[:-1])
    user.last_name = data['fullname'].split()[-1]

    # Try to retrieve username from NTNUs LDAP server. Otherwise use the first part of the email as the username
    ldap_data = get_user_details_from_email(user.email, use_cached=False)
    if ldap_data:
        user.username = ldap_data["username"]
    else:
        user.username = user.email.split('@')[0]

    user.save()

    return response
