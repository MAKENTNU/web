from django.http import JsonResponse
import subprocess

LDAP_HOST = 'at.ntnu.no'

fields = {
    'full_name': 'gecos',
    'surname': 'sn',
    'group_id': 'gidNumber',
    'id': 'uidNumber',
    'username': 'uid',
}


def LDAP_search(field, value):
    return subprocess.check_output(["ldapsearch", "-h", LDAP_HOST, '-x', '{}={}'.format(field, value)]).decode()


def get_LDAP_field(ldapData, field):
    name_start = ldapData.find(field + ': ') + len(field + ': ')
    return ldapData[name_start:ldapData.find('\n', name_start)]


def get_full_name_from_username(request, username):
    return JsonResponse({
        "full_name": get_LDAP_field(LDAP_search(fields['username'], username), fields['full_name']),
        "username": username,
    })
