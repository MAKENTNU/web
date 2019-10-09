from django.forms.widgets import NumberInput


class CardNumberInput(NumberInput):
    template_name = "card/card_number_input.html"
