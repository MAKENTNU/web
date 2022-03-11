from abc import ABC

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, DeleteView, TemplateView, UpdateView
from django.views.generic.edit import ModelFormMixin

from users.models import User
from util.view_utils import CustomFieldsetFormMixin, PreventGetRequestsMixin
from ...forms import QuotaForm
from ...models.reservation import Quota


class QuotaPanelView(TemplateView):
    """View for the quota admin panel that allows users to control the quotas of people."""
    template_name = 'make_queue/quota/quota_panel.html'

    def get_context_data(self, user=None, **kwargs):
        """
        Creates the required context for the quota panel.

        :return: A list of all users
        """
        return super().get_context_data(**{
            'users': User.objects.all(),
            'global_quotas': Quota.objects.filter(all=True),
            'requested_user': user,
            **kwargs,
        })


class QuotaFormMixin(CustomFieldsetFormMixin, ModelFormMixin, ABC):
    model = Quota
    form_class = QuotaForm

    narrow = False
    centered_title = False
    custom_fieldsets = [
        {'fields': ('number_of_reservations', 'machine_type'), 'layout_class': "two"},
        {'fields': ('diminishing', 'ignore_rules', 'all'), 'layout_class': "inline"},
        {'fields': ('user',)},
    ]

    def get_back_button_link(self):
        return reverse('quota_panel')

    def get_back_button_text(self):
        return _("Admin page for quotas")

    def get_success_url(self):
        if self.object.all:
            return reverse('quota_panel')
        else:
            return reverse('quota_panel', kwargs={'user': self.object.user})


class CreateQuotaView(PermissionRequiredMixin, QuotaFormMixin, CreateView):
    permission_required = ('make_queue.add_quota',)

    form_title = _("New Quota")
    save_button_text = _("Add")


class EditQuotaView(PermissionRequiredMixin, QuotaFormMixin, UpdateView):
    permission_required = ('make_queue.change_quota',)

    form_title = _("Edit Quota")

    def get_back_button_link(self):
        return self.get_success_url()

    def get_back_button_text(self):
        if self.object.all:
            return _("Admin page for quotas")
        else:
            return _("Admin page for the quotas of {user_full_name}").format(
                user_full_name=self.object.user.get_full_name(),
            )


class DeleteQuotaView(PermissionRequiredMixin, PreventGetRequestsMixin, DeleteView):
    permission_required = ('make_queue.delete_quota',)
    model = Quota

    def get_success_url(self):
        if self.object.all:
            return reverse('quota_panel')
        else:
            return reverse('quota_panel', kwargs={'user': self.object.user})
