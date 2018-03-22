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

    def handle(self, user):
        if user.username in self.allowed_users and not Quota3D.get_quota(user).can_print:
            quota = Quota3D.get_quota(user)
            quota.can_print = True
            quota.save()

    def update(self):
        if "queue_token" not in dir(web.settings):
            return
        response = post(self.data_url, {"token": web.settings.queue_token})
        try:
            self.allowed_users = response.json()["allowed"]
        except JSONDecodeError:
            pass

    def __init__(self):
        self.update()


register_handler(PrinterHandler, "printer_allowed")
