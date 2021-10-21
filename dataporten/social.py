from social_core.backends.oauth import BaseOAuth2
from social_core.exceptions import AuthException


class DataportenOAuth2(BaseOAuth2):
    name = 'dataporten'
    ID_KEY = 'userid'
    REQUIRES_EMAIL_VALIDATION = False
    EXTRA_DATA = [
        # (<name from Dataporten's API>, <alias for storage in the database and usage in e.g. views>)
        ('userid', 'userid'),
        ('scope', 'scope'),
        ('name', 'fullname'),
        ('email', 'email'),
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
        Return user details from Dataporten.
        """
        user = response
        # <Convert response data from Dataporten's format to a format fit for usage in e.g. views, here>
        return user

    def check_correct_audience(self, audience):
        """Assert that Dataporten sends back our own client ID as audience."""
        client_id, _ = self.get_key_and_secret()
        if audience != client_id:
            raise AuthException('Wrong audience')

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
            'Refresh tokens for Dataporten have not been implemented'
        )
