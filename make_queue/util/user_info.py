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
    'mail': 'mail',
}


def LDAP_search(field, value):
    l = ldap.initialize(LDAP_HOST, bytes_mode=False)
    l.simple_bind()
    query = "({}={})".format(LDAP_FIELDS[field], value)
    return l.search_s(LDAP_BASE, ldap.SCOPE_SUBTREE, query)


def get_LDAP_field(ldapData, field):
    return ldapData[0][1].get(LDAP_FIELDS[field], [b''])[0].decode()
    # list<tuple<str, dict<str, list<bstr>>>>


def get_user_details_from_username(username):
    user_details = {"username": username}
    user = User.objects.filter(username=username).first()
    if user:
        user_details["full_name"] = user.get_full_name()
        user_details["email"] = user.email
    else:
        ldap_results = LDAP_search("username", username)
        if len(ldap_results) == 0:
            return None
        user_details["full_name"] = get_LDAP_field(ldap_results, "full_name")
        user_details["email"] = get_LDAP_field(ldap_results, "mail")

    return user_details


def get_user_details_from_email(email):
    user = User.objects.filter(email=email).first()
    if user:
        return get_user_details_from_username(username=user.username)

    ldap_results = LDAP_search("mail", email)
    if len(ldap_results) == 0:
        return None
    return get_user_details_from_username(get_LDAP_field(ldap_results, "username"))
