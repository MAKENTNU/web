from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views import View

from web import settings


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
        card_id = request.POST.get('card_id')
        if secret is None or card_id is None:
            return HttpResponse(status=400)

        if secret == settings.CHECKIN_KEY:
            if len(card_id) == 10 and card_id.isnumeric():
                return self.card_id_valid(card_id)
            else:
                return self.card_id_invalid(card_id)
        return HttpResponse(status=403)

    def card_id_valid(self, card_id):
        """
        Handles the case where the card id is valid.
        Should be overridden in a subclass.
        :param card_id: The card id from the request, prefixed with EM
        :return: An HttpResponse
        """
        return HttpResponse(status=200)

    def card_id_invalid(self, card_id):
        """
        Handles the case where the card id is invalid.
        Should be overridden in a subclass.
        :param card_id: The card id from the request, prefixed with EM
        :return: An HttpResponse
        """
        return HttpResponse(status=401)
