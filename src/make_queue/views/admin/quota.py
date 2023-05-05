from abc import ABC

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models.functions import Concat
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, DeleteView, TemplateView, UpdateView
from django.views.generic.edit import ModelFormMixin

from users.models import User
from util.view_utils import CustomFieldsetFormMixin, PreventGetRequestsMixin
from ...forms import QuotaForm
from ...models.reservation import Quota


class AdminQuotaPanelView(PermissionRequiredMixin, TemplateView):
    """View for the quota admin panel that allows users to control the quotas of people."""
    permission_required = ('make_queue.change_quota',)
    template_name = 'make_queue/quota/admin_quota_panel.html'

    user: User | None

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        if 'pk' in self.kwargs:
            user_pk = self.kwargs['pk']
            self.user = get_object_or_404(User, pk=user_pk)
        else:
            self.user = None

    def get_context_data(self, **kwargs):
        """
        Creates the required context for the quota panel.

        :return: A list of all users
        """
        return super().get_context_data(**{
            'users': User.objects.order_by(Concat('first_name', 'last_name'), 'username'),
            'global_quotas': Quota.objects.filter(all=True),
            'requested_user': self.user,
            **kwargs,
        })


class QuotaFormMixin(CustomFieldsetFormMixin, ModelFormMixin, ABC):
    model = Quota
    form_class = QuotaForm

    narrow = False
    centered_title = False
    custom_fieldsets = [
        {'fields': ('number_of_reservations', 'machine_type'), 'layout_class': "ui two fields"},
        {'fields': ('diminishing', 'ignore_rules', 'all'), 'layout_class': "ui inline fields"},
        {'fields': ('user',)},
    ]

    def get_back_button_link(self):
        return reverse('admin_quota_panel')

    def get_back_button_text(self):
        return _("Admin page for quotas")

    def get_success_url(self):
        if self.object.all:
            return reverse('admin_quota_panel')
        else:
            return reverse('admin_quota_panel', args=[self.object.user.pk])


class QuotaCreateView(PermissionRequiredMixin, QuotaFormMixin, CreateView):
    permission_required = ('make_queue.add_quota',)

    form_title = _("Add Quota")
    save_button_text = _("Add")


class QuotaUpdateView(PermissionRequiredMixin, QuotaFormMixin, UpdateView):
    permission_required = ('make_queue.change_quota',)

    form_title = _("Change Quota")

    def get_back_button_link(self):
        return self.get_success_url()

    def get_back_button_text(self):
        if self.object.all:
            return _("Admin page for quotas")
        else:
            return _("Admin page for the quotas of {user_full_name}").format(
                user_full_name=self.object.user.get_full_name(),
            )


class QuotaDeleteView(PermissionRequiredMixin, PreventGetRequestsMixin, DeleteView):
    permission_required = ('make_queue.delete_quota',)
    model = Quota

    def get_success_url(self):
        if self.object.all:
            return reverse('admin_quota_panel')
        else:
            return reverse('admin_quota_panel', args=[self.object.user.pk])
