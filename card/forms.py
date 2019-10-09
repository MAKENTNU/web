from django.forms import IntegerField

from card.widgets import CardNumberInput


class CardNumberField(IntegerField):
    widget = CardNumberInput
