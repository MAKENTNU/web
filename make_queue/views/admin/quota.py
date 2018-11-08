from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.auth.models import User
from django.urls import reverse
from django.views.generic import TemplateView, CreateView, UpdateView, DeleteView

from make_queue.forms import QuotaForm
from make_queue.models.models import Quota


class QuotaView(TemplateView):
    """View for the quota admin panel that allows users to control the quotas of people"""
    template_name = "make_queue/quota/quota_panel.html"

    def get_context_data(self, user=None, **kwargs):
        """
        Creates the required context for the quota panel

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
    model = Quota
    form_class = QuotaForm
    template_name = "make_queue/quota/quota_create.html"
    permission_required = (
        "make_queue.add_quota",
    )

    def get_success_url(self):
        if self.object.all:
            return reverse("quota_panel")
        return reverse("quota_panel", kwargs={"user": self.object.user})


class EditQuotaView(PermissionRequiredMixin, UpdateView):
    model = Quota
    template_name = "make_queue/quota/quota_edit.html"
    form_class = QuotaForm
    permission_required = (
        "make_queue.change_quota",
    )

    def get_success_url(self):
        if self.object.all:
            return reverse("quota_panel")
        return reverse("quota_panel", kwargs={"user": self.object.user})


class DeleteQuotaView(PermissionRequiredMixin, DeleteView):
    model = Quota
    permission_required = (
        "make_queue.delete_quota",
    )

    def get_success_url(self):
        if self.object.all:
            return reverse("quota_panel")
        return reverse("quota_panel", kwargs={"user": self.object.user})
