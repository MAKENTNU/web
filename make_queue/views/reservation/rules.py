from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse
from django.views.generic import TemplateView, DeleteView, CreateView, UpdateView

from ...forms import RuleForm
from ...models.models import MachineType, MachineUsageRule, Quota, ReservationRule


class RulesOverviewView(TemplateView):
    template_name = "make_queue/rule_list.html"

    def get_context_data(self, machine_type: MachineType, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data.update({
            "machine_type": machine_type,
            "rules": machine_type.reservation_rules.all(),
        })
        if not self.request.user.is_anonymous:
            context_data.update({
                "quotas": Quota.get_user_quotas(self.request.user, machine_type),
            })
        return context_data


class CreateReservationRuleView(PermissionRequiredMixin, CreateView):
    permission_required = ("make_queue.add_reservation_rule",)
    model = ReservationRule
    form_class = RuleForm
    template_name = "make_queue/rule_create.html"

    def get_success_url(self):
        return reverse("machine_rules", args=[self.object.machine_type])


class EditReservationRuleView(PermissionRequiredMixin, UpdateView):
    permission_required = ("make_queue.change_reservation_rule",)
    model = ReservationRule
    form_class = RuleForm
    template_name = "make_queue/rule_edit.html"

    def get_success_url(self):
        return reverse("machine_rules", args=[self.object.machine_type])


class DeleteReservationRules(PermissionRequiredMixin, DeleteView):
    permission_required = ("make_queue.delete_reservation_rule",)
    model = ReservationRule

    def get_success_url(self):
        return reverse("machine_rules", args=[self.object.machine_type])


class MachineUsageRulesView(TemplateView):
    template_name = "make_queue/usage_rules_detail.html"

    def get_context_data(self, machine_type, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data.update({
            "usage_rules": MachineUsageRule.objects.get_or_create(machine_type=machine_type)[0],
        })
        return context_data


class EditUsageRulesView(PermissionRequiredMixin, UpdateView):
    permission_required = ('make_queue.change_machineusagerule',)
    model = MachineUsageRule
    fields = ('content',)
    template_name = 'make_queue/usage_rules_edit.html'
    context_object_name = 'usage_rule'

    def get_success_url(self):
        return reverse("machine_usage_rules", args=[self.object.machine_type])
