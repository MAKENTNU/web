"""
Note: querying NTNU's LDAP server requires connection to NTNU's VPN.
"""
import ldap

from users.models import User


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

STANDARD_USER_DETAILS_FIELDS = ('username', 'email', 'full_name')


def ldap_search(search_field: str, search_value: str) -> list[tuple[str, dict[str, list[bytes]]]]:
    """
    Searches the LDAP server given by LDAP_HOST with the filter ``search_field=search_value``.

    :return: List of results returned by the LDAP server. Each item in the list is a tuple with distinguished name
             and a dictionary with the attributes of the user.
    """
    ldap_obj = ldap.initialize(LDAP_HOST, bytes_mode=False)
    ldap_obj.simple_bind()
    query = f"({LDAP_FIELDS[search_field]}={search_value})"
    return ldap_obj.search_s(LDAP_BASE, ldap.SCOPE_SUBTREE, query)


def get_ldap_field(ldap_data: list[tuple[str, dict[str, list[bytes]]]], field: str) -> str:
    """
    Retrieves the value of a field in ``ldap_data``.

    :param ldap_data: Results from ldap_search(). List of tuples with distinguished name and dictionary of attributes.
    :param field: Field in ldap_data whose value is to be returned.
    :return: Value of field in ldap_data. Empty string if the field does not exist.
    """
    return ldap_data[0][1].get(LDAP_FIELDS[field], [b''])[0].decode()


def get_user_details_from_ldap(search_field: str, search_value: str) -> dict[str, str]:
    """
    Retrieves all relevant user details from LDAP.
    Searches the LDAP server given by LDAP_HOST with the filter ``search_field=search_value``.

    :return: Dictionary with user details. (full name, username, email)
    """
    ldap_data = ldap_search(search_field, search_value)
    if ldap_data:
        return {field: get_ldap_field(ldap_data, field) for field in STANDARD_USER_DETAILS_FIELDS}
    return {}


def _get_user_details_from_user_field(field_name: str, field_value: str, use_cached: bool) -> dict[str, str]:
    user_details = {}
    if use_cached:
        user = User.objects.filter(**{field_name: field_value}).first()
        if user:
            user_details = {
                'username': user.username,
                'email': user.email,
                'full_name': user.get_full_name(),
            }

    if (user_details
            # If `user_details` contains values for all dict keys:
            and all(value for value in user_details.values())):
        return user_details

    try:
        ldap_user_details = get_user_details_from_ldap(field_name, field_value)
    except ldap.LDAPError:
        return user_details

    if not ldap_user_details:
        return user_details
    if not user_details:
        return ldap_user_details

    # Update missing values with data from LDAP
    for key, value in user_details.items():
        if not value:
            user_details[key] = ldap_user_details[key]
    return user_details


def get_user_details_from_username(username: str, use_cached=True) -> dict[str, str]:
    """
    Retrieves details for user given by username, either from database or LDAP server.

    :param username: username of user to find
    :param use_cached: Whether to search database before performing an LDAP search
    :return: Dictionary with user details. (full name, username, email)
    """
    return _get_user_details_from_user_field('username', username, use_cached)


def get_user_details_from_email(email: str, use_cached=True) -> dict[str, str]:
    """
    Retrieves details for user given by email, either from database or LDAP server.

    :param email: email of user to find
    :param use_cached: Whether to search database before performing an LDAP search
    :return: Dictionary with user details. (full name, username, email)
    """
    return _get_user_details_from_user_field('email', email, use_cached)
