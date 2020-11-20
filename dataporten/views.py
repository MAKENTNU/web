import logging

from django.conf import settings
from django.contrib.auth import logout
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.views import View
from social_django import views as social_views

from users.models import User
from . import ldap_utils

# Assign these functions to module-level variables, to facilitate testing (through monkey patching)
complete = social_views.complete
get_user_details_from_email = ldap_utils.get_user_details_from_email


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
    except Exception as e:
        logging.getLogger('django.request').exception("Authentication through Dataporten failed.", exc_info=e)
        return HttpResponseForbidden()

    user: User = request.user
    social_data = user.social_auth.first().extra_data

    # If any of the user's names have not been set...
    if (not user.get_full_name() or not user.ldap_full_name
            # ...or if the user has not set a different name after account creation:
            or user.get_full_name().strip() == user.ldap_full_name.strip()):
        _update_full_name_if_different(user, social_data)
    # Update the LDAP name after the full name has (potentially) been set.
    # This is only important if the user has not logged in before, as the full name has not yet been set.
    _update_ldap_full_name_if_different(user, social_data)

    # Try to retrieve username from NTNUs LDAP server. Otherwise use the first part of the email as the username
    ldap_data = get_user_details_from_email(user.email, use_cached=False)
    _update_username_if_different(user, ldap_data)

    return response


def _update_full_name_if_different(user: User, social_data: dict):
    split_ldap_name = social_data['fullname'].split()
    old_full_name = user.get_full_name()
    user.first_name = " ".join(split_ldap_name[:-1])
    user.last_name = split_ldap_name[-1]
    if user.get_full_name() != old_full_name:
        user.save()


def _update_ldap_full_name_if_different(user: User, social_data: dict):
    if user.ldap_full_name != social_data['fullname']:
        user.ldap_full_name = social_data['fullname']
        user.save()


def _update_username_if_different(user: User, ldap_data: dict):
    potentially_new_username = ldap_data['username'] if ldap_data else user.email.split("@")[0]
    if user.username != potentially_new_username:
        user.username = potentially_new_username
        user.save()
