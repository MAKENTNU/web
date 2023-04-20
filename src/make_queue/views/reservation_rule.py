from abc import ABC

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, DeleteView, ListView, UpdateView
from django.views.generic.edit import ModelFormMixin

from users.models import User
from util.view_utils import CustomFieldsetFormMixin, PreventGetRequestsMixin, insert_form_field_values
from ..forms.reservation_rule import ReservationRuleForm
from ..models.reservation import Quota, ReservationRule
from ..views.machine import MachineTypeRelatedViewMixin


class ReservationRuleListView(MachineTypeRelatedViewMixin, ListView):
    model = ReservationRule
    template_name = 'make_queue/reservation_rule_list.html'
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
        user: User = self.request.user
        if user.is_authenticated:
            context_data.update({
                'quotas': Quota.get_user_quotas(user, self.machine_type),
            })
            if user.has_any_permissions_for(ReservationRule):
                context_data.update({
                    'rule_set_has_gaps': ReservationRule.rule_set_has_gaps(self.machine_type),
                })
        return context_data


class ReservationRuleFormMixin(MachineTypeRelatedViewMixin, CustomFieldsetFormMixin, ModelFormMixin, ABC):
    model = ReservationRule
    form_class = ReservationRuleForm

    narrow = False
    centered_title = False
    custom_fieldsets = [
        {'fields': ('start_time', 'days_changed', 'end_time'), 'layout_class': "ui three fields"},
        {'fields': ('start_days', 'max_hours', 'max_inside_border_crossed'), 'layout_class': "ui three fields"},
    ]

    def get_queryset(self):
        return self.machine_type.reservation_rules.all()

    def get_form_kwargs(self):
        # Forcefully pass the machine type from the URL to the form
        return insert_form_field_values(super().get_form_kwargs(), {'machine_type': self.machine_type.pk})

    def get_back_button_link(self):
        return self.get_success_url()

    def get_back_button_text(self):
        return _("Reservation rules for {machine_type}").format(machine_type=self.machine_type)

    def get_success_url(self):
        return reverse('reservation_rule_list', args=[self.machine_type.pk])


class ReservationRuleCreateView(PermissionRequiredMixin, ReservationRuleFormMixin, CreateView):
    permission_required = ('make_queue.add_reservationrule',)

    save_button_text = _("Add")

    def get_form_title(self):
        return _("Add Rule for {machine_type}").format(machine_type=self.machine_type)


class ReservationRuleUpdateView(PermissionRequiredMixin, ReservationRuleFormMixin, UpdateView):
    permission_required = ('make_queue.change_reservationrule',)
    pk_url_kwarg = 'reservation_rule_pk'

    def get_form_title(self):
        return _("Change Rule for {machine_type}").format(machine_type=self.machine_type)


class ReservationRuleDeleteView(PermissionRequiredMixin, PreventGetRequestsMixin, DeleteView):
    permission_required = ('make_queue.delete_reservationrule',)
    model = ReservationRule
    pk_url_kwarg = 'reservation_rule_pk'

    def get_success_url(self):
        return reverse('reservation_rule_list', args=[self.object.machine_type.pk])
