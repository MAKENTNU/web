from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from util.view_utils import PreventGetRequestsMixin
from ...forms import BaseMachineForm, EditMachineForm
from ...models.models import Machine, MachineType


class MachineView(ListView):
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


class CreateMachineView(PermissionRequiredMixin, CreateView):
    permission_required = ('make_queue.add_machine',)
    model = Machine
    form_class = BaseMachineForm
    template_name = 'make_queue/machine/machine_create.html'
    success_url = reverse_lazy("reservation_machines_overview")

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["has_stream_dict"] = {machine_type.pk: machine_type.has_stream for machine_type in MachineType.objects.all() }
        return context_data


class EditMachineView(PermissionRequiredMixin, UpdateView):
    permission_required = ('make_queue.change_machine',)
    model = Machine
    form_class = EditMachineForm
    template_name = 'make_queue/machine/machine_edit.html'
    success_url = reverse_lazy("reservation_machines_overview")

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data['has_stream_dict'] = {
            machine_type.pk: machine_type.has_stream for machine_type in MachineType.objects.all()
        }
        return context_data


class DeleteMachineView(PermissionRequiredMixin, PreventGetRequestsMixin, DeleteView):
    permission_required = ('make_queue.delete_machine',)
    model = Machine
    success_url = reverse_lazy("reservation_machines_overview")
