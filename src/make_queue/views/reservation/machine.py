from abc import ABC

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from util.view_utils import CustomFieldsetFormMixin, PreventGetRequestsMixin
from ...forms import AddMachineForm, ChangeMachineForm, ReservationListQueryForm
from ...models.machine import Machine, MachineType


class MachineListView(ListView):
    """View that shows all the machines -- listed per machine type."""
    model = MachineType
    template_name = 'make_queue/machine_list.html'
    context_object_name = 'machine_types'
    extra_context = {
        'ReservationOwner': ReservationListQueryForm.Owner,
    }

    def get_queryset(self):
        machine_queryset = Machine.objects.visible_to(self.request.user).default_order_by()
        return MachineType.objects.default_order_by().prefetch_machines(
            machine_queryset=machine_queryset, machines_attr_name='shown_machines',
        )


class MachineFormMixin(CustomFieldsetFormMixin, ABC):
    model = Machine
    success_url = reverse_lazy('machine_list')

    narrow = False
    back_button_link = success_url
    back_button_text = _("Machine list")

    should_include_machine_type: bool

    def get_custom_fieldsets(self):
        return [
            {'fields': ('machine_type' if self.should_include_machine_type else None, 'machine_model'), 'layout_class': "ui two fields"},
            {'fields': ('name',), 'layout_class': "ui two fields"},
            {'fields': ('stream_name',), 'layout_class': "ui two fields"} if self.should_include_stream_name() else None,
            {'fields': ('location', 'location_url'), 'layout_class': "ui two fields"},
            {'fields': ('priority', 'status'), 'layout_class': "ui two fields"},
            {'fields': ('info_message', 'info_message_date'), 'layout_class': "ui two fields"},
            {'fields': ('internal',), 'layout_class': "ui segment field"},
            {'fields': ('notes',)},
        ]

    def should_include_stream_name(self):
        return True


class MachineCreateView(PermissionRequiredMixin, MachineFormMixin, CreateView):
    permission_required = ('make_queue.add_machine',)
    form_class = AddMachineForm

    form_title = _("Add Machine")
    save_button_text = _("Add")

    should_include_machine_type = True


class MachineUpdateView(PermissionRequiredMixin, MachineFormMixin, UpdateView):
    permission_required = ('make_queue.change_machine',)
    form_class = ChangeMachineForm

    form_title = _("Change Machine")

    should_include_machine_type = False

    def should_include_stream_name(self):
        return self.object.machine_type.has_stream


class MachineDeleteView(PermissionRequiredMixin, PreventGetRequestsMixin, DeleteView):
    permission_required = ('make_queue.delete_machine',)
    model = Machine
    success_url = reverse_lazy('machine_list')
