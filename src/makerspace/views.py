from abc import ABC

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from contentbox.views import ContentBoxDetailView
from util.templatetags.string_tags import title_en
from util.view_utils import CustomFieldsetFormMixin, PreventGetRequestsMixin
from .forms import EquipmentForm
from .models import Equipment


class MakerspaceView(ContentBoxDetailView):
    template_name = 'makerspace/makerspace.html'


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
        return self.request.user.has_any_permissions_for(Equipment)


class EquipmentFormMixin(CustomFieldsetFormMixin, ABC):
    model = Equipment
    form_class = EquipmentForm
    success_url = reverse_lazy('admin_equipment_list')

    back_button_link = success_url
    back_button_text = _("Admin page for equipment")


class EquipmentCreateView(PermissionRequiredMixin, EquipmentFormMixin, CreateView):
    permission_required = ('makerspace.add_equipment',)

    save_button_text = _("Add")

    def get_form_title(self):
        return title_en(_("Add equipment"))


class EquipmentUpdateView(PermissionRequiredMixin, EquipmentFormMixin, UpdateView):
    permission_required = ('makerspace.change_equipment',)

    form_title = _("Change Equipment")


class EquipmentDeleteView(PermissionRequiredMixin, PreventGetRequestsMixin, DeleteView):
    permission_required = ('makerspace.delete_equipment',)
    model = Equipment
    success_url = reverse_lazy('admin_equipment_list')
