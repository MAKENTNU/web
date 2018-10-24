from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse
from django.views.generic import TemplateView, DeleteView, CreateView, UpdateView

from make_queue.forms import RuleForm
from make_queue.models.models import ReservationRule, Quota


class RulesOverviewView(TemplateView):
    template_name = "make_queue/rules.html"

    def get_context_data(self, machine_type, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data.update({
            "rules": ReservationRule.objects.filter(machine_type=machine_type),
        })
        if not self.request.user.is_anonymous:
            context_data.update({
                "quotas": Quota.get_user_quotas(self.request.user, machine_type),
            })
        return context_data


class CreateReservationRuleView(PermissionRequiredMixin, CreateView):
    model = ReservationRule
    template_name = "make_queue/rule_create.html"
    form_class = RuleForm
    permission_required = (
        "make_queue.add_reservation_rule",
    )

    def get_success_url(self):
        return reverse("machine_rules", args=[self.object.machine_type])


class EditReservationRuleView(PermissionRequiredMixin, UpdateView):
    model = ReservationRule
    template_name = "make_queue/rule_edit.html"
    form_class = RuleForm
    permission_required = (
        "make_queue.change_reservation_rule",
    )

    def get_success_url(self):
        return reverse("machine_rules", args=[self.object.machine_type])


class DeleteReservationRules(PermissionRequiredMixin, DeleteView):
    model = ReservationRule
    permission_required = (
        "make_queue.delete_reservation_rule",
    )

    def get_success_url(self):
        return reverse("machine_rules", args=[self.object.machine_type])
