from django.contrib.auth.models import User
from django.views.generic import TemplateView


class QuotaView(TemplateView):
    """View for the quota admin panel that allows users to control the quotas of people"""
    template_name = "make_queue/quota_panel.html"

    def get_context_data(self):
        """
        Creates the required context for the quota panel

        :return: A list of all users
        """
        return {"users": User.objects.all()}
