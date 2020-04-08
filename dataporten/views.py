import logging

from django.conf import settings
from django.contrib.auth import logout
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.views import View
from social_core.exceptions import AuthException
from social_django.views import complete

from dataporten.ldap_utils import get_user_details_from_email


class Logout(View):

    def get(self, request):
        logout(request)
        return HttpResponseRedirect(settings.LOGOUT_URL)


def login_wrapper(request, backend, *args, **kwargs):
    """
    Handles the callback from the social django login. Updating the full name of the user, and possibly their username.
    Usernames are found in NTNUs LDAP server using the email to search. For some reason, some users do not have their
    email in the NTNU LDAP system. For these users we derive their username from the local part of their email. This
    will be the correct NTNU username for all students. We have yet to find an employee without their email in LDAP.

    :return: The landing page after login, as defined by the social django configuration.
    """
    try:
        response = complete(request, backend, *args, **kwargs)
    except AuthException as e:
        logging.warning("Authentication through Dataporten failed.", e)
        return HttpResponseForbidden()

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
