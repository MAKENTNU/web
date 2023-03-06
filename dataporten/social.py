from social_core.backends.oauth import BaseOAuth2
from social_core.exceptions import AuthException


# Code based on https://github.com/Uninett/python-dataporten-auth/blob/bad1b95483c5da7d279df4a8d542a3c24c928095/src/dataporten/social.py
class DataportenOAuth2(BaseOAuth2):
    name = 'dataporten'
    ID_KEY = 'userid'
    REQUIRES_EMAIL_VALIDATION = False
    EXTRA_DATA = [
        # (<name returned by `get_user_details()`>, <alias for storage in the database - through `UserSocialAuth.extra_data`>)
        ('scope', 'scope'),
        ('userid', 'userid'),
        ('username', 'username'),  # used as the base username for new users; it's set in `get_user_details()` below
        ('email', 'email'),
        ('name', 'fullname'),
    ]
    BASE_URL = 'https://auth.dataporten.no'
    API_URL = 'https://api.dataporten.no'
    AUTHORIZATION_URL = f'{BASE_URL}/oauth/authorization'
    ACCESS_TOKEN_METHOD = 'POST'
    ACCESS_TOKEN_URL = f'{BASE_URL}/oauth/token'
    STATE_PARAMETER = True
    REDIRECT_STATE = False

    def auth_complete_credentials(self):
        return self.get_key_and_secret()

    def get_user_details(self, response):
        """
        Converts response data from the format of Dataporten's API, to the format expected by the ``social`` libraries -
        which is stored in ``UserSocialAuth.extra_data`` (through ``EXTRA_DATA`` above).

        :return: user details from Dataporten.
        """
        user = response

        # Based on https://github.com/Uninett/python-dataporten-auth/blob/bad1b95483c5da7d279df4a8d542a3c24c928095/src/dataporten/social.py#L102-L107
        for userid in user['userid_sec']:
            usertype, complete_username = userid.split(':')
            if usertype == 'feide':
                username, _domain = complete_username.split('@')
                user['username'] = username
                break

        return user

    def check_correct_audience(self, audience):
        """Assert that Dataporten sends back our own client ID as audience."""
        client_id, _ = self.get_key_and_secret()
        if audience != client_id:
            raise AuthException("Wrong audience")

    def user_data(self, access_token, *args, **kwargs):
        """Loads user data from service."""
        url = f'{self.BASE_URL}/userinfo'
        response = self.get_json(
            url,
            headers={'Authorization': f'Bearer {access_token}'},
        )
        self.check_correct_audience(response['audience'])

        userdata = response['user']
        return userdata

    def refresh_token(self, *args, **kwargs):
        raise NotImplementedError(
            "Refresh tokens for Dataporten have not been implemented"
        )
