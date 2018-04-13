from django.contrib.auth.models import User
from django.urls import reverse_lazy
from django.views.generic import TemplateView, RedirectView

from dataporten.login_handlers import get_handler


class QuotaView(TemplateView):
    """View for the quota admin panel that allows users to control the quotas of people"""
    template_name = "make_queue/quota_panel.html"

    def get_context_data(self):
        """
        Creates the required context for the quota panel

        :return: A list of all users
        """
        return {"users": User.objects.all()}


class UpdatePrinterHandlerView(RedirectView):
    """View for forcing an update for the login handler responsible for booking permissions"""
    url = reverse_lazy("quota_panel")

    def dispatch(self, request, *args, **kwargs):
        """Force update the login handler for all requests"""
        get_handler("printer_allowed").update()
        return super().dispatch(self, request, *args, **kwargs)
