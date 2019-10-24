import requests

"""
Module for testing the RFID functionality on makentnu.no when running locally and/or without an RFID scanner.
"""


def _card(path, card_id, secret):
    r = requests.post(
        "http://makentnu.local.test.pe:8000/" + path,
        headers={"Content-type": "application/x-www-form-urlencoded"},
        data={"card_id": card_id, "secret": secret}
    )
    return r.status_code, r.text


def register(card_id="0123456789", secret=""):
    return _card("checkin/register/card/", card_id, secret)


def check(card_id="0123456789", secret=""):
    return _card("checkin/post/", card_id, secret)
