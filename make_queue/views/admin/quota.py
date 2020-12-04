from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse
from django.views.generic import CreateView, DeleteView, TemplateView, UpdateView

from users.models import User
from util.view_utils import PreventGetRequestsMixin
from ...forms import QuotaForm
from ...models.reservation import Quota


class QuotaView(TemplateView):
    """View for the quota admin panel that allows users to control the quotas of people."""
    template_name = 'make_queue/quota/quota_panel.html'

    def get_context_data(self, user=None, **kwargs):
        """
        Creates the required context for the quota panel.

        :return: A list of all users
        """
        context_data = super().get_context_data(**kwargs)
        context_data.update({
            "users": User.objects.all(),
            "global_quotas": Quota.objects.filter(all=True),
            "requested_user": user,
        })
        return context_data


class CreateQuotaView(PermissionRequiredMixin, CreateView):
    permission_required = ("make_queue.add_quota",)
    model = Quota
    form_class = QuotaForm
    template_name = 'make_queue/quota/quota_create.html'

    def get_success_url(self):
        if self.object.all:
            return reverse("quota_panel")
        else:
            return reverse("quota_panel", kwargs={"user": self.object.user})


class EditQuotaView(PermissionRequiredMixin, UpdateView):
    permission_required = ("make_queue.change_quota",)
    model = Quota
    form_class = QuotaForm
    template_name = 'make_queue/quota/quota_edit.html'

    def get_success_url(self):
        if self.object.all:
            return reverse("quota_panel")
        else:
            return reverse("quota_panel", kwargs={"user": self.object.user})


class DeleteQuotaView(PermissionRequiredMixin, PreventGetRequestsMixin, DeleteView):
    permission_required = ("make_queue.delete_quota",)
    model = Quota

    def get_success_url(self):
        if self.object.all:
            return reverse("quota_panel")
        else:
            return reverse("quota_panel", kwargs={"user": self.object.user})
