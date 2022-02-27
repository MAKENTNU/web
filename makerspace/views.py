from abc import ABC

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from contentbox.views import DisplayContentBoxView
from util.templatetags.permission_tags import has_any_equipment_permissions
from util.view_utils import CustomFieldsetFormMixin, PreventGetRequestsMixin
from .forms import EquipmentForm
from .models import Equipment


class MakerspaceView(DisplayContentBoxView):
    template_name = 'makerspace/makerspace.html'
    title = 'makerspace'


class EquipmentDetailView(DetailView):
    model = Equipment
    template_name = 'makerspace/equipment/equipment_detail.html'
    context_object_name = 'equipment'


class EquipmentListView(ListView):
    model = Equipment
    queryset = Equipment.objects.default_order_by()
    template_name = 'makerspace/equipment/equipment_list.html'
    context_object_name = 'equipment_list'


class AdminEquipmentListView(PermissionRequiredMixin, ListView):
    model = Equipment
    queryset = Equipment.objects.default_order_by()
    template_name = 'makerspace/equipment/admin_equipment_list.html'
    context_object_name = 'equipment_list'

    def has_permission(self):
        return has_any_equipment_permissions(self.request.user)


class EquipmentFormMixin(CustomFieldsetFormMixin, ABC):
    model = Equipment
    form_class = EquipmentForm
    success_url = reverse_lazy('makerspace_admin_equipment_list')

    back_button_link = success_url
    back_button_text = _("Admin page for equipment")


class CreateEquipmentView(PermissionRequiredMixin, EquipmentFormMixin, CreateView):
    permission_required = ('makerspace.add_equipment',)

    form_title = _("New Equipment")


class EditEquipmentView(PermissionRequiredMixin, EquipmentFormMixin, UpdateView):
    permission_required = ('makerspace.change_equipment',)

    form_title = _("Edit Equipment")


class DeleteEquipmentView(PermissionRequiredMixin, PreventGetRequestsMixin, DeleteView):
    permission_required = ('makerspace.delete_equipment',)
    model = Equipment
    success_url = reverse_lazy('makerspace_admin_equipment_list')
