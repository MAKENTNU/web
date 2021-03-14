from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import TemplateView, CreateView, UpdateView, DeleteView

from ...forms import BaseMachineForm, EditMachineForm
from ...models.models import Machine, MachineType


class MachineView(TemplateView):
    """View that shows all the machines"""
    template_name = "make_queue/machine_list.html"

    def get_context_data(self):
        """
        Creates the context required for the template.

        :return: A queryset of all machine types which have at least one existing machine.
        """
        return {
            "machine_types": MachineType.objects.prefetch_machines_and_default_order_by(machines_attr_name="existing_machines")
                .filter(machines__isnull=False).distinct(),  # filtering through a many-related field (`machines`) can cause duplicates
        }


class CreateMachineView(PermissionRequiredMixin, CreateView):
    permission_required = ('make_queue.add_machine',)
    model = Machine
    form_class = BaseMachineForm
    template_name = "make_queue/machine/machine_create.html"
    success_url = reverse_lazy("reservation_machines_overview")


class EditMachineView(PermissionRequiredMixin, UpdateView):
    permission_required = ('make_queue.change_machine',)
    model = Machine
    form_class = EditMachineForm
    template_name = "make_queue/machine/machine_edit.html"
    success_url = reverse_lazy("reservation_machines_overview")


class DeleteMachineView(PermissionRequiredMixin, DeleteView):
    permission_required = ('make_queue.delete_machine',)
    model = Machine
    success_url = reverse_lazy("reservation_machines_overview")
