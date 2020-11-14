from abc import ABC

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView
from django.views.generic.base import ContextMixin
from django.views.generic.edit import ModelFormMixin

from ...forms import RuleForm
from ...models.models import MachineType, MachineUsageRule, Quota, ReservationRule


class MachineTypeBasedView(ContextMixin, View, ABC):
    machine_type: MachineType

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.machine_type = kwargs['machine_type']

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data.update({
            'machine_type': self.machine_type,
        })
        return context_data


class RulesOverviewView(MachineTypeBasedView, ListView):
    model = ReservationRule
    template_name = 'make_queue/rule_list.html'
    context_object_name = 'rules'

    def get_queryset(self):
        return self.machine_type.reservation_rules.all()

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        if not self.request.user.is_anonymous:
            context_data.update({
                'quotas': Quota.get_user_quotas(self.request.user, self.machine_type),
            })
        return context_data


class BaseReservationRulePostView(ModelFormMixin, ABC):
    model = ReservationRule
    form_class = RuleForm
    context_object_name = 'rule'

    def get_success_url(self):
        return reverse('machine_rules', args=[self.object.machine_type])


class CreateReservationRuleView(PermissionRequiredMixin, BaseReservationRulePostView, CreateView):
    permission_required = ('make_queue.add_reservation_rule',)
    template_name = 'make_queue/rule_create.html'


class EditReservationRuleView(PermissionRequiredMixin, BaseReservationRulePostView, UpdateView):
    permission_required = ('make_queue.change_reservation_rule',)
    template_name = 'make_queue/rule_edit.html'


class DeleteReservationRules(PermissionRequiredMixin, DeleteView):
    permission_required = ('make_queue.delete_reservation_rule',)
    model = ReservationRule

    def get_success_url(self):
        return reverse('machine_rules', args=[self.object.machine_type])


class MachineUsageRulesView(MachineTypeBasedView, DetailView):
    model = MachineUsageRule
    template_name = 'make_queue/usage_rules_detail.html'
    context_object_name = 'usage_rules'

    def get_object(self, queryset=None):
        usage_rule, _created = MachineUsageRule.objects.get_or_create(machine_type=self.machine_type)
        return usage_rule


class EditUsageRulesView(PermissionRequiredMixin, UpdateView):
    permission_required = ('make_queue.change_machineusagerule',)
    model = MachineUsageRule
    fields = ('content',)
    template_name = 'make_queue/usage_rules_edit.html'
    context_object_name = 'usage_rule'

    def get_success_url(self):
        return reverse('machine_usage_rules', args=[self.object.machine_type])
