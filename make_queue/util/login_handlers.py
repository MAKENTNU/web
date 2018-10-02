from json import JSONDecodeError

from dataporten.login_handlers import LoginHandler
from requests import post
import web.settings


class PrinterHandler(LoginHandler):
    """Handles retrieving who are allowed to book the 3D printers from a remote service"""
    allowed_users = []
    data_url = "https://script.google.com/a/makentnu.no/macros/s/AKfycbxXpV5Ew6VeuRF7klHTMr55X7lXmOLkPjZeV8kVOipXSnoRiFCl/exec"

    def __init__(self):
        self.token = None
        # Check if there exists some token for the remote service
        if "queue_token" in dir(web.settings):
            self.token = web.settings.queue_token
            # Need to retrieve allowed users on creation
            self.update()

    def handle(self, user):
        """
        Whenever this is called it checks if the user is allowed to book the 3D printers and checks that against the
        current system permissions. If the user is allowed remote, but not locally the local settings are changed
        :param user: The user to check permissions for
        """
        pass
        """
        if user.username in self.allowed_users and not Quota3D.get_quota(user).can_print:
            quota = Quota3D.get_quota(user)
            quota.can_print = True
            quota.save()"""

    def is_correct_token(self, token):
        """
        Checks if the given token is the correct token for the printer handler
        :param token: The token to check
        :return: A boolean indicating if the token is correct
        """
        return self.token is not None and token == self.token

    def update(self):
        """Retrieves and updates the list of allowed users from the remote service"""
        if self.token is None:
            raise ValueError("No valid token")

        response = post(self.data_url, {"token": self.token})
        try:
            self.allowed_users = response.json()["allowed"]
        except JSONDecodeError:
            pass
