from django.http import JsonResponse
import ldap

LDAP_HOST = 'ldap://at.ntnu.no'
LDAP_BASE = 'dc=ntnu, dc=no'

fields = {
    'full_name': 'cn',
    'surname': 'sn',
    'group_id': 'gidNumber',
    'id': 'uidNumber',
    'username': 'uid',
}


def LDAP_search(field, value):
    l = ldap.initialize(LDAP_HOST)
    l.simple_bind()
    query = "({}={})".format(field, value)
    return l.search_s(LDAP_BASE, ldap.SCOPE_SUBTREE, query)


def get_LDAP_field(ldapData, field):
    if len(ldapData) == 0: # No results
        return ""
    return ldapData[0][1][field][0].decode()


def get_user_details_from_username(request, username):
    return JsonResponse({
        "full_name": get_LDAP_field(LDAP_search(fields['username'], username), fields['full_name']),
        "username": username,
    })
