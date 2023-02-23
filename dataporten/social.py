from social_core.backends.open_id_connect import OpenIdConnectAuth


# Code based on https://github.com/Uninett/python-dataporten-auth/blob/bad1b95483c5da7d279df4a8d542a3c24c928095/src/dataporten/social.py
class DataportenOAuth2(OpenIdConnectAuth):
    name = 'dataporten'
    OIDC_ENDPOINT = 'https://auth.dataporten.no'
    DEFAULT_SCOPE = OpenIdConnectAuth.DEFAULT_SCOPE + [
        # These attribute groups (among others) are selected in the "User information" tab of our website's service in Feide's customer portal
        'userinfo-name',  # From the customer portal: "Given name, surname, legal name, common name and display name"
        'userid-feide',  # From the customer portal: "User name, personal Feide ID at organization and previous Feide IDs at organization"
    ]
    # Names of extra claims (keys in the response dict from Dataporten) to store in the database
    # - through the `extra_data` field on the `UserSocialAuth` model (e.g. `user.social_auth.first().extra_data`).
    # If a list element is a tuple, it's interpreted like this:
    # (<claim name - returned by `get_user_details()`>, <key for the JSON key/value pair stored through `extra_data`>)
    EXTRA_DATA = OpenIdConnectAuth.EXTRA_DATA + [
        'scope',
        'username',  # used as the base username for new users; it's set in `get_user_details()` below
        'email',
        ('name', 'fullname'),
    ]
    # Name of the claim containing the secondary user ID
    # (see https://docs.feide.no/reference/oauth_oidc/openid_connect_details.html#id-token)
    USERID_SEC_CLAIM_NAME = 'https://n.feide.no/claims/userid_sec'

    def get_user_details(self, response):
        """
        Converts response data from the format of Dataporten's API, to the format used by the rest of the code.

        See info on the API endpoint here: https://docs.feide.no/reference/apis/userinfo.html

        :return: user details from Dataporten.
        """
        user = super().get_user_details(response)

        # Based on https://github.com/Uninett/python-dataporten-auth/blob/bad1b95483c5da7d279df4a8d542a3c24c928095/src/dataporten/social.py#L102-L107
        for userid in response[self.USERID_SEC_CLAIM_NAME]:
            usertype, complete_username = userid.split(':')
            if usertype == 'feide':
                username, _domain = complete_username.split('@')
                user['username'] = username
                break

        return user

    def refresh_token(self, *args, **kwargs):
        raise NotImplementedError(
            "Refresh tokens for Dataporten have not been implemented"
        )
