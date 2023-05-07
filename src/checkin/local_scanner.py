import requests
from django.urls import reverse

"""
Module for testing the RFID functionality on makentnu.no when running locally and/or without an RFID scanner.
"""


def _card(path, card_id, secret):
    r = requests.post(
        f"http://makentnu.local.test.pe:8000/{path}",
        headers={"Content-type": "application/x-www-form-urlencoded"},
        data={"card_id": card_id, "secret": secret}
    )
    return r.status_code, r.text


def register(card_id="0123456789", secret=""):
    return _card(reverse('admin_register_card'), card_id, secret)


def check(card_id="0123456789", secret=""):
    return _card(reverse('admin_check_in'), card_id, secret)
