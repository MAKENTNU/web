from django.urls import reverse_lazy
from django.views.generic import TemplateView, CreateView, UpdateView, DeleteView

from make_queue.fields import MachineTypeField
from make_queue.models.models import Machine


class MachineView(TemplateView):
    """View that shows all the machines"""
    template_name = "make_queue/reservation_machines.html"

    def get_context_data(self):
        """
        Creates the context required for the template

        :return: A list of all machine types with a list of their machine if there exists at least one machine of that
                type
        """
        return {"machine_types": [{
            "name": machine_type.name,
            "machines": list(Machine.objects.filter(machine_type=machine_type)),
            "type": machine_type,
        } for machine_type in MachineTypeField.possible_machine_types if
            Machine.objects.filter(machine_type=machine_type).exists()]}


class CreateMachineView(CreateView):
    template_name = "make_queue/machine/machine_create.html"
    model = Machine
    fields = '__all__'


class EditMachineView(UpdateView):
    template_name = "make_queue/machine/machine_edit.html"
    model = Machine
    fields = '__all__'


class DeleteMachineView(DeleteView):
    model = Machine
    success_url = reverse_lazy("reservation_machines_overview")
