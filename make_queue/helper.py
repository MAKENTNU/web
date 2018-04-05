from json import JSONDecodeError

import pytz
from django.utils import timezone
from dataporten.login_handlers import LoginHandler, register_handler
from make_queue.models import Quota3D
from requests import post
import web.settings


def date_to_local(date):
    return timezone.localtime(date, timezone.get_default_timezone())


def local_to_date(date):
    return pytz.timezone(timezone.get_default_timezone_name()).localize(date)


class PrinterHandler(LoginHandler):
    allowed_users = []
    data_url = "https://script.google.com/a/makentnu.no/macros/s/AKfycbxXpV5Ew6VeuRF7klHTMr55X7lXmOLkPjZeV8kVOipXSnoRiFCl/exec"

    def __init__(self):
        self.token = None
        if "queue_token" in dir(web.settings):
            self.token = web.settings.queue_token
            self.update()

    def handle(self, user):
        if user.username in self.allowed_users and not Quota3D.get_quota(user).can_print:
            quota = Quota3D.get_quota(user)
            quota.can_print = True
            quota.save()

    def is_correct_token(self, token):
        return self.token is not None and token == self.token

    def update(self):
        if self.token is None:
            raise ValueError("No valid token")

        response = post(self.data_url, {"token": self.token})
        try:
            self.allowed_users = response.json()["allowed"]
        except JSONDecodeError:
            pass


register_handler(PrinterHandler, "printer_allowed")
