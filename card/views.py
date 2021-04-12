from django.conf import settings
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from . import utils


@method_decorator(csrf_exempt, name="dispatch")
class RFIDView(View):
    """
    Base view class for receiving requests from RFID card readers.
    """

    def post(self, request):
        """
        Handles the request from the RFID card reader.
        Does a basic check for a valid card id.

        :param request: The HTTP POST request to handle. Must include a secret and the card id.
        :return: An HttpResponse.
        """
        secret = request.POST.get('secret')
        card_number = request.POST.get('card_id')
        if secret is None or card_number is None:
            return HttpResponse(status=400)

        if secret == settings.CHECKIN_KEY:
            if utils.is_valid(card_number):
                return self.card_number_valid(card_number)
            else:
                return self.card_number_invalid(card_number)
        return HttpResponse(status=403)

    def card_number_valid(self, card_number):
        """
        Handles the case where the card number is valid.
        Should be overridden in a subclass.

        :param card_number: The card id from the request
        :return: An HttpResponse
        """
        return HttpResponse(f"Valid card number {card_number}", status=200)

    def card_number_invalid(self, card_number):
        """
        Handles the case where the card number is invalid.
        Should be overridden in a subclass.

        :param card_number: The card id from the request
        :return: An HttpResponse
        """
        return HttpResponse(f"Invalid card number {card_number}", status=401)
