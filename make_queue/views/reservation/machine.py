from abc import ABC

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from util.view_utils import CustomFieldsetFormMixin, PreventGetRequestsMixin
from ...forms import BaseMachineForm, EditMachineForm
from ...models.machine import Machine, MachineType


class MachineListView(ListView):
    """View that shows all the machines - listed per machine type."""
    model = MachineType
    queryset = (
        # Retrieves all machine types that have at least one existing machine
        MachineType.objects.prefetch_machines_and_default_order_by(
            machines_attr_name='existing_machines',
        ).filter(machines__isnull=False).distinct()  # remove duplicates that can appear when filtering on values across tables
    )
    template_name = 'make_queue/machine_list.html'
    context_object_name = 'machine_types'


class MachineFormMixin(CustomFieldsetFormMixin, ABC):
    model = Machine
    success_url = reverse_lazy('machine_list')

    narrow = False
    back_button_link = success_url
    back_button_text = _("Machine list")

    should_include_machine_type: bool

    def get_custom_fieldsets(self):
        return [
            {'fields': ('name', 'machine_type' if self.should_include_machine_type else None), 'layout_class': "two"},
            {'fields': ('machine_model',), 'layout_class': "two"},
            {'fields': ('location', 'location_url'), 'layout_class': "two"},
            {'fields': ('priority', 'status'), 'layout_class': "two"},
        ]


class CreateMachineView(PermissionRequiredMixin, MachineFormMixin, CreateView):
    permission_required = ('make_queue.add_machine',)
    form_class = BaseMachineForm

    form_title = _("Create Machine")
    save_button_text = _("Add")

    should_include_machine_type = True


class EditMachineView(PermissionRequiredMixin, MachineFormMixin, UpdateView):
    permission_required = ('make_queue.change_machine',)
    form_class = EditMachineForm

    form_title = _("Edit Machine")

    should_include_machine_type = False


class DeleteMachineView(PermissionRequiredMixin, PreventGetRequestsMixin, DeleteView):
    permission_required = ('make_queue.delete_machine',)
    model = Machine
    success_url = reverse_lazy('machine_list')
