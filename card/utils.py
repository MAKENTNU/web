from django.core.exceptions import ValidationError

from make_queue.models.course import Printer3DCourse
from users.models import User
from .formfields import CardNumberField


def is_valid(card_number):
    """
    Checks if value is a valid card number by running all card number validators.
    :param card_number: The card number to check
    :return: True if value passes all validators
    """
    for validator in CardNumberField.default_validators:
        try:
            validator(card_number)
        except ValidationError:
            return False
    return True


def is_duplicate(card_number, username):
    """
    Checks if given card number is a duplicate. Excludes card number connected to user with given username.
    :param card_number: card number to check if duplicate
    :param username: username of user to exclude
    :return: True if card_number is duplicate
    """
    return User.objects.filter(card_number=card_number).exclude(username=username).exists() \
        or Printer3DCourse.objects.filter(_card_number=card_number).exclude(username=username).exists()
