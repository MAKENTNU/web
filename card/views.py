from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views import View

from web import settings
from card.models import Card


class RFIDView(View):
    """
    Base view class for receiving requests from RFID card readers
    """

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    @csrf_exempt
    def post(self, request):
        """
        Handles the request from the RFID card reader.
        Does a basic check for a valid card id.
        :param request: The HTTP POST request to handle. Must include a secret and the card id.
        :return: An HttpResponse.
        """
        secret = request.POST.get('secret')
        card_number = request.POST.get('card_number')
        if secret is None or card_number is None:
            return HttpResponse(status=400)

        if secret == settings.CHECKIN_KEY:
            if Card.is_valid(card_number):
                return self.card_number_valid(card_number)
            else:
                return self.card_number_invalid(card_number)
        return HttpResponse(status=403)

    def card_number_valid(self, card_number):
        """
        Handles the case where the card id is valid.
        Should be overridden in a subclass.
        :param card_number: The card id from the request
        :return: An HttpResponse
        """
        return HttpResponse(f"Valid card number {card_number}", status=200)

    def card_number_invalid(self, card_number):
        """
        Handles the case where the card id is invalid.
        Should be overridden in a subclass.
        :param card_number: The card id from the request
        :return: An HttpResponse
        """
        return HttpResponse(f"Invalid card number {card_number}", status=401)
