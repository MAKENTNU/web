from abc import ABC

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse_lazy
from django.db.models import Prefetch, Count, F, Sum, IntegerField, Q
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView, TemplateView

from contentbox.views import ContentBoxDetailView
from util.templatetags.string_tags import title_en
from util.view_utils import CustomFieldsetFormMixin, PreventGetRequestsMixin
from .forms import EquipmentForm
from .models import Equipment
from make_queue.models.reservation import Reservation
from make_queue.models.machine import Machine


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


class StatisticsView(TemplateView):
    template_name = 'makerspace/statistics.html'
    get_time_in_hours = 3600000000  # number the reservation length needs to be divided by to get the length in hours
    filter_reservations = Q(reservations__special=False) & Q(reservations__event__isnull=True)

    reservations = Reservation.objects.prefetch_related(Prefetch('machine', queryset=Machine.objects.
                                                                 prefetch_related('machine_type'))).filter(special=False).annotate(
        q_overnight=Sum(F('start_time__hour') - F('end_time__hour')))

    sewingmachines = Machine.objects.prefetch_related('machine_type', 'reservation').filter(
        Q(machine_type__name__icontains="Symaskiner") & filter_reservations).annotate(
        len=(Sum((F('reservations__end_time') - F('reservations__start_time')) / get_time_in_hours, output_field=IntegerField()))).annotate(
        number_of_reservations=Count('reservations'))

    printers = Machine.objects.prefetch_related('machine_type', 'reservation').filter(
        Q(machine_type__name__icontains="3D-printere") & filter_reservations).annotate(
        len=(Sum((F('reservations__end_time') - F('reservations__start_time')) / get_time_in_hours, output_field=IntegerField()))).annotate(
        number_of_reservations=Count('reservations'))

    def get_time_distribution(self):
        overnight = self.reservations.filter(q_overnight__gte=0)  # reservations overnight has to be counted differently
        not_overnight = self.reservations.exclude(q_overnight__gte=0)
        time = {}
        for r in range(0, 24):
            time[r] = not_overnight.filter(Q(start_time__hour__lte=r) & Q(end_time__hour__gte=(r - 1))).count()
            time[r] += overnight.filter(Q(start_time__hour__lte=r) | Q(end_time__hour__gte=(r - 1))).count()
        return dict(time.items())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        span_of_printer_reservations = list(self.printers.values('id', 'name', 'len'))
        number_of_printer_reservations = list(self.printers.values('id', 'name', 'number_of_reservations'))
        longest_printer_reservations = list(self.printers.order_by('-len').values('id', 'name', 'reservations', 'len'))[:3]
        span_of_sewingmachine_reservations = list(self.sewingmachines.values('id', 'name', 'len'))
        number_of_sewingmachine_reservations = list(self.sewingmachines.values('id', 'name', 'number_of_reservations'))
        get_time_distribution = self.get_time_distribution()
        context.update({'span_of_printer_reservations': span_of_printer_reservations,
                        'span_of_sewingmachine_reservations': span_of_sewingmachine_reservations,
                        'longest_printer_reservations': longest_printer_reservations,
                        'number_of_printer_reservations': number_of_printer_reservations,
                        'number_of_sewingmachine_reservations': number_of_sewingmachine_reservations,
                        'time': get_time_distribution, })
        return context
