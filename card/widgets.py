from django.forms.widgets import TextInput


class CardNumberInput(TextInput):
    template_name = 'card/widgets/card_number_input.html'
