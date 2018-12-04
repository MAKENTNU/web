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


def LDAP_search(search_field, search_value):
    """
    Searches the LDAP server given by LDAP_HOST with the filter search_field=search_value
    :return: List of results returned by the LDAP server. Each item in the list is a tuple with distinguished name
    and a dictionary with the attributes of the user.
    """
    l = ldap.initialize(LDAP_HOST, bytes_mode=False)
    l.simple_bind()
    query = "({}={})".format(LDAP_FIELDS[search_field], search_value)
    return l.search_s(LDAP_BASE, ldap.SCOPE_SUBTREE, query)


def get_LDAP_field(ldap_data, field):
    """
    Retrieves tha value of a field in LDAP data
    :param ldap_data: Results from LDAP_search. List of tuples with distinguished name and dictionary of attributes.
    :param field: Field in ldap_data whose value is to be returned.
    :return: Value of field in ldap_data. Empty string if the field does not exist.
    """
    return ldap_data[0][1].get(LDAP_FIELDS[field], [b''])[0].decode()


def get_user_details_from_LDAP(search_field, search_value):
    """
    Retrieves all relevant user details from LDAP.
    Searches the LDAP server given by LDAP_HOST with the filter search_field=search_value
    :return: Dictionary with user details. (full name, username, email)
    """
    ldap_data = LDAP_search(search_field, search_value)
    if ldap_data:
        return {field: get_LDAP_field(ldap_data, field) for field in ("full_name", "username", "email")}
    return {}


def get_user_details_from_username(username, use_cached=True):
    """
    Retrieves details for user given by username, either from database or LDAP server
    :param username: username of user to find
    :param use_cached: Whether to search datebase before performing a LDAP search
    :return: Dictionary with user details. (full name, username, email)
    """
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
    """
        Retrieves details for user given by email, either from database or LDAP server
        :param email: email of user to find
        :param use_cached: Whether to search datebase before performing a LDAP search
        :return: Dictionary with user details. (full name, username, email)
        """
    if use_cached:
        user = User.objects.filter(email=email).first()
        if user:
            return {
                "username": user.username,
                "full_name": user.get_full_name(),
                "email": email,
            }
    return get_user_details_from_LDAP("mail", email)
