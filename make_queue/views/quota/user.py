from django.views.generic import ListView

from users.models import User
from ...models.reservation import Quota


class UserQuotaListView(ListView):
    """View for getting a rendered version of the quota of a specific user."""
    model = Quota
    template_name = 'make_queue/quota/quota_user.html'
    context_object_name = 'user_quotas'

    def get_queryset(self):
        user: User = self.kwargs['user']
        return user.quotas.filter(all=False)
