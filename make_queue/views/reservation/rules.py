from abc import ABC

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView
from django.views.generic.base import ContextMixin
from django.views.generic.edit import ModelFormMixin

from util.view_utils import CustomFieldsetFormMixin, PreventGetRequestsMixin, insert_form_field_values
from ...forms import ReservationRuleForm
from ...models.machine import MachineType, MachineUsageRule
from ...models.reservation import Quota, ReservationRule


class MachineTypeBasedView(ContextMixin, View, ABC):
    machine_type: MachineType

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.machine_type = kwargs['machine_type']

    def get_context_data(self, **kwargs):
        return super().get_context_data(**{
            'machine_type': self.machine_type,
            **kwargs,
        })


class ReservationRuleListView(MachineTypeBasedView, ListView):
    model = ReservationRule
    template_name = 'make_queue/rule_list.html'
    context_object_name = 'rules'

    def get_queryset(self):
        return self.machine_type.reservation_rules.all()

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**{
            # This translation is here instead of in the template, to avoid two translation entries
            # differing only in format syntax (`{var}` vs `%(var)s`)
            'title': _("Reservation rules for {machine_type}").format(machine_type=self.machine_type),
            **kwargs,
        })
        if self.request.user.is_authenticated:
            context_data.update({
                'quotas': Quota.get_user_quotas(self.request.user, self.machine_type),
            })
        return context_data


class BaseReservationRuleEditView(MachineTypeBasedView, CustomFieldsetFormMixin, ModelFormMixin, ABC):
    model = ReservationRule
    form_class = ReservationRuleForm

    narrow = False
    centered_title = False
    custom_fieldsets = [
        {'fields': ('start_time', 'days_changed', 'end_time'), 'layout_class': "three"},
        {'fields': ('start_days', 'max_hours', 'max_inside_border_crossed'), 'layout_class': "three"},
    ]

    def get_queryset(self):
        return self.machine_type.reservation_rules.all()

    def get_form_kwargs(self):
        # Forcefully pass the machine type from the URL to the form
        return insert_form_field_values(super().get_form_kwargs(), ('machine_type', self.machine_type.pk))

    def get_back_button_link(self):
        return self.get_success_url()

    def get_back_button_text(self):
        return _("Reservation rules for {machine_type}").format(machine_type=self.machine_type)

    def get_success_url(self):
        return reverse('reservation_rule_list', args=[self.machine_type])


class CreateReservationRuleView(PermissionRequiredMixin, BaseReservationRuleEditView, CreateView):
    permission_required = ('make_queue.add_reservation_rule',)

    def get_form_title(self):
        return _("New Rule for {machine_type}").format(machine_type=self.machine_type)


class EditReservationRuleView(PermissionRequiredMixin, BaseReservationRuleEditView, UpdateView):
    permission_required = ('make_queue.change_reservation_rule',)

    def get_form_title(self):
        return _("Rule for {machine_type}").format(machine_type=self.machine_type)


class DeleteReservationRuleView(PermissionRequiredMixin, PreventGetRequestsMixin, DeleteView):
    permission_required = ('make_queue.delete_reservation_rule',)
    model = ReservationRule

    def get_success_url(self):
        return reverse('reservation_rule_list', args=[self.object.machine_type])


class MachineUsageRulesDetailView(MachineTypeBasedView, DetailView):
    model = MachineUsageRule
    template_name = 'make_queue/usage_rules_detail.html'
    context_object_name = 'usage_rules'

    def get_object(self, queryset=None):
        usage_rule, _created = MachineUsageRule.objects.get_or_create(machine_type=self.machine_type)
        return usage_rule

    def get_context_data(self, **kwargs):
        return super().get_context_data(**{
            # This translation is here instead of in the template, to avoid two translation entries
            # differing only in format syntax (`{var}` vs `%(var)s`)
            'title': _("Usage rules for {machine_type}").format(machine_type=self.machine_type),
            **kwargs,
        })


class EditUsageRulesView(PermissionRequiredMixin, MachineTypeBasedView, UpdateView):
    permission_required = ('make_queue.change_machineusagerule',)
    model = MachineUsageRule
    fields = ('content',)
    template_name = 'make_queue/usage_rules_edit.html'
    context_object_name = 'usage_rule'

    def get_object(self, queryset=None):
        return self.machine_type.usage_rule

    def get_success_url(self):
        return reverse('machine_usage_rules_detail', args=[self.object.machine_type])
