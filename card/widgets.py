from django.forms.widgets import TextInput

from .modelfields import CardNumber


class CardNumberInput(TextInput):
    template_name = 'card/widgets/card_number_input.html'

    def format_value(self, value):
        if isinstance(value, CardNumber):
            return value.number
        return super().format_value(value)
