from django.contrib.auth.models import User
import ldap

LDAP_HOST = 'ldap://at.ntnu.no'
LDAP_BASE = 'dc=ntnu, dc=no'

LDAP_FIELDS = {
    'full_name': 'cn',
    'surname': 'sn',
    'group_id': 'gidNumber',
    'id': 'uidNumber',
    'username': 'uid',
    'email': 'mail',
}


def LDAP_search(field, value):
    l = ldap.initialize(LDAP_HOST, bytes_mode=False)
    l.simple_bind()
    query = "({}={})".format(LDAP_FIELDS[field], value)
    return l.search_s(LDAP_BASE, ldap.SCOPE_SUBTREE, query)


def get_LDAP_field(ldapData, field):
    return ldapData[0][1].get(LDAP_FIELDS[field], [b''])[0].decode()
    # list<tuple<str, dict<str, list<bstr>>>>


def get_user_details_from_LDAP(search_field, search_value):
    ldap_data = LDAP_search(search_field, search_value)
    if ldap_data:
        return {field: get_LDAP_field(ldap_data, field) for field in ("full_name", "username", "email")}
    return {}


def get_user_details_from_username(username, use_cached=True):
    if use_cached:
        user = User.objects.filter(username=username).first()
        if user:
            return {
                "username": username,
                "full_name": user.get_full_name(),
                "email": user.email,
            }
    return get_user_details_from_LDAP("username", username)


def get_user_details_from_email(email, use_cached=True):
    if use_cached:
        user = User.objects.filter(email=email).first()
        if user:
            return {
                "username": user.username,
                "full_name": user.get_full_name(),
                "email": email,
            }
    return get_user_details_from_LDAP("mail", email)
