from django.views.generic import TemplateView

from users.models import User


class GetUserQuotaView(TemplateView):
    """View for getting a rendered version of the quota of a specific user."""
    template_name = 'make_queue/quota/quota_user.html'

    def get_context_data(self, user: User, **kwargs):
        """
        Creates the context required for the template.

        :param user: The user for which to get the quota
        :return: The context
        """
        return {
            "user_quotas": user.quotas.filter(all=False),
        }
