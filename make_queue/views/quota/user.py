from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import get_object_or_404
from django.views.generic import ListView

from users.models import User
from ...models.reservation import Quota


class UserQuotaListView(PermissionRequiredMixin, ListView):
    """View for getting a rendered version of the quota of a specific user."""
    permission_required = ('make_queue.change_quota',)
    model = Quota
    template_name = 'make_queue/quota/quota_user.html'
    context_object_name = 'user_quotas'

    user: User

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        user_pk = self.kwargs['pk']
        self.user = get_object_or_404(User, pk=user_pk)

    def get_queryset(self):
        return self.user.quotas.filter(all=False)
