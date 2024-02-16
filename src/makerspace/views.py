from abc import ABC

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from contentbox.models import ContentBox
from contentbox.views import ContentBoxDetailView
from util.templatetags.string_tags import title_en
from util.view_utils import CustomFieldsetFormMixin, PreventGetRequestsMixin
from .forms import CardNumberUpdateForm, EquipmentForm
from .models import Equipment
from make_queue.models.course import Printer3DCourse
from users.models import User


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


@method_decorator(login_required, name="dispatch")
class CardRegistrationView(UpdateView):
    model = User
    form_class = CardNumberUpdateForm
    template_name = 'makerspace/card_registration/card_registration.html'
    url_name = 'card_registration'

    def get_object(self, queryset=None):
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        contentbox, _created = ContentBox.objects.get_or_create(url_name=self.url_name)
        context['contentbox'] = contentbox
        return context

    def form_valid(self, form):
        action_choice = self.request.POST['action']
        if action_choice == '2' or action_choice == '3':
            try:
                user_course_registration = Printer3DCourse.objects.get(user=self.request.user)
                user_course_registration.status = Printer3DCourse.Status.REGISTERED
                user_course_registration.save()
            except Printer3DCourse.DoesNotExist:
                pass
        return super().form_valid(form)

    def get_success_url(self):
        success_url = reverse_lazy('card_registration')
        success_url += '?success=true'
        return success_url
