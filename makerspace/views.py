from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from contentbox.views import DisplayContentBoxView
from util.views import PreventGetRequestsMixin
from web.templatetags.permission_tags import has_any_equipment_permissions
from .forms import EquipmentForm
from .models import Equipment


class MakerspaceView(DisplayContentBoxView):
    template_name = "makerspace/makerspace.html"
    title = 'makerspace'


class EquipmentView(DetailView):
    model = Equipment
    template_name = "makerspace/equipment/equipment.html"
    context_object_name = 'equipment'


class EquipmentListView(ListView):
    model = Equipment
    queryset = Equipment.objects.default_order_by()
    template_name = "makerspace/equipment/equipment_list.html"
    context_object_name = 'equipment_list'


class AdminEquipmentView(PermissionRequiredMixin, ListView):
    model = Equipment
    queryset = Equipment.objects.default_order_by()
    template_name = "makerspace/equipment/admin_equipment.html"
    context_object_name = 'equipment_list'

    def has_permission(self):
        return has_any_equipment_permissions(self.request.user)


class CreateEquipmentView(PermissionRequiredMixin, CreateView):
    permission_required = ('makerspace.add_equipment',)
    model = Equipment
    form_class = EquipmentForm
    template_name = "makerspace/equipment/admin_equipment_create.html"
    context_object_name = 'equipment'
    success_url = reverse_lazy('makerspace-equipment-admin')


class EditEquipmentView(PermissionRequiredMixin, UpdateView):
    permission_required = ('makerspace.change_equipment',)
    model = Equipment
    form_class = EquipmentForm
    template_name = "makerspace/equipment/admin_equipment_edit.html"
    context_object_name = 'equipment'
    success_url = reverse_lazy('makerspace-equipment-admin')

    # Delete the old image file if a new image is being uploaded:
    def form_valid(self, form):
        if form.files.get('image'):
            equipment = self.get_object()
            equipment.image.delete()
        return super().form_valid(form)


class DeleteEquipmentView(PermissionRequiredMixin, PreventGetRequestsMixin, DeleteView):
    permission_required = ('makerspace.delete_equipment',)
    model = Equipment
    success_url = reverse_lazy('makerspace-equipment-admin')

    # Delete the image file before deleting the object:
    def delete(self, request, *args, **kwargs):
        equipment = self.get_object()
        equipment.image.delete()
        return super().delete(request, *args, **kwargs)
