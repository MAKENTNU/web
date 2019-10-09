from django.forms import CharField

from card.widgets import CardNumberInput


class CardNumberField(CharField):
    widget = CardNumberInput

