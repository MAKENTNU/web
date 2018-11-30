from django.http import JsonResponse
from django.contrib.auth.models import User
from django.http import HttpResponseNotFound
import ldap

LDAP_HOST = 'ldap://at.ntnu.no'
LDAP_BASE = 'dc=ntnu, dc=no'

fields = {
    'full_name': 'cn',
    'surname': 'sn',
    'group_id': 'gidNumber',
    'id': 'uidNumber',
    'username': 'uid',
    'mail': 'mail',
}


def LDAP_search(field, value):
    l = ldap.initialize(LDAP_HOST, bytes_mode=False)
    l.simple_bind()
    query = "({}={})".format(fields[field], value)
    return l.search_s(LDAP_BASE, ldap.SCOPE_SUBTREE, query)


def get_LDAP_field(ldapData, field):
    return ldapData[0][1].get(fields[field], [""])[0].decode()
    # list<tuple<str, dict<str, list<str>>>>

def get_user_details_from_username(request, username):
    user = User.objects.filter(username=username).first()
    user_details = {"username": username}
    if user:
        user_details["full_name"] = user.get_full_name()
        user_details["email"] = user.email
    else:
        ldap_results = LDAP_search("username", username)
        if len(ldap_results) == 0:
            return HttpResponseNotFound()
        user_details["full_name"] = get_LDAP_field(ldap_results, "full_name")
        user_details["email"] = get_LDAP_field(ldap_results, "mail")

    return JsonResponse(user_details)

def get_user_details_from_email(request, email):
    user = User.objects.filter(email=email).first()
    if user:
        return get_user_details_from_username(username=user.username)

    ldap_results = LDAP_search("mail", email)
    if len(ldap_results) == 0:
        return HttpResponseNotFound()
    return get_user_details_from_username(request, get_LDAP_field(ldap_results, "username"))