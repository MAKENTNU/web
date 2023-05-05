import io

import xlsxwriter
from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import redirect
from django.template.defaultfilters import capfirst
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, DeleteView, ListView, UpdateView, View

from util.view_utils import PreventGetRequestsMixin
from ...forms import Printer3DCourseForm
from ...models.course import Printer3DCourse


class Printer3DCourseListView(PermissionRequiredMixin, ListView):
    permission_required = ('make_queue.view_printer3dcourse', 'make_queue.change_printer3dcourse')
    model = Printer3DCourse
    queryset = Printer3DCourse.objects.select_related('user').order_by('name')
    template_name = 'make_queue/course/printer_3d_course_list.html'
    context_object_name = 'registrations'
    extra_context = {
        'possible_statuses': Printer3DCourse.Status.choices,
    }


class Printer3DCourseCreateView(PermissionRequiredMixin, CreateView):
    permission_required = ('make_queue.add_printer3dcourse',)
    model = Printer3DCourse
    form_class = Printer3DCourseForm
    template_name = 'make_queue/course/printer_3d_course_create.html'
    # Redirect back to the same view, to make it easier to create multiple registrations
    success_url = reverse_lazy('printer_3d_course_create')

    def form_valid(self, form):
        messages.success(self.request, _("Registration of course participation successful"))
        return super().form_valid(form)


class Printer3DCourseUpdateView(PermissionRequiredMixin, UpdateView):
    permission_required = ('make_queue.change_printer3dcourse',)
    model = Printer3DCourse
    form_class = Printer3DCourseForm
    template_name = 'make_queue/course/printer_3d_course_form.html'
    success_url = reverse_lazy('printer_3d_course_list')


class Printer3DCourseDeleteView(PermissionRequiredMixin, PreventGetRequestsMixin, DeleteView):
    permission_required = ('make_queue.delete_printer3dcourse',)
    model = Printer3DCourse
    success_url = reverse_lazy('printer_3d_course_list')


class Printer3DCourseStatusBulkUpdateView(PermissionRequiredMixin, View):
    """
    Provides a method for bulk-updating the status of course registrations.
    """
    permission_required = ('make_queue.change_printer3dcourse',)

    def post(self, request):
        status = request.POST.get('status')
        registrations = list(map(int, request.POST.getlist('users')))
        Printer3DCourse.objects.filter(pk__in=registrations).update(status=status)

        return redirect('printer_3d_course_list')


class Printer3DCourseXLSXView(PermissionRequiredMixin, View):
    permission_required = ('make_queue.change_printer3dcourse',)

    def post(self, request):
        search_string = request.POST.get('search_text')
        status_filter = request.POST.get('status_filter')
        selected = request.POST.get('selected')

        # If selected is set, we want to include only these registrations
        if selected:
            course_registrations = Printer3DCourse.objects.filter(pk__in=selected.split(","))
        else:
            course_registrations = Printer3DCourse.objects.filter(
                Q(username__icontains=search_string) | Q(name__icontains=search_string),
                status__icontains=status_filter)
        course_registrations = course_registrations.select_related('user')

        # Use an in-memory output file, to avoid having to clean up the disk
        output_file = io.BytesIO()

        workbook = xlsxwriter.Workbook(output_file, {'in_memory': True})
        worksheet = workbook.add_worksheet(str(_("Course participants")))

        # Styles
        format_header = workbook.add_format({
            "bold": True,
            "font_size": 10,
            "font_name": "Arial",
            "font_color": "#000000",
            "bg_color": "#F8C811",
            "border": 1,
            "border_color": "#000000",
        })

        format_row = workbook.add_format({
            "font_size": 10,
            "font_name": "Arial",
            "font_color": "#000000",
            "bg_color": "#FFF2CC",
            "border": 1,
            "border_color": "#000000",
        })

        # Set column width
        worksheet.set_column("A:A", 40)
        worksheet.set_column("B:B", 20)
        worksheet.set_column("C:C", 15)
        worksheet.set_column("D:D", 10)

        # Header
        # `capfirst()` to avoid duplicate translation differing only in case
        worksheet.write(0, 0, capfirst(_("name")), format_header)
        worksheet.write(0, 1, capfirst(_("username")), format_header)
        worksheet.write(0, 2, capfirst(_("card number")), format_header)
        worksheet.write(0, 3, capfirst(_("date")), format_header)

        for index, registration in enumerate(course_registrations):
            worksheet.write(index + 1, 0, registration.name, format_row)
            worksheet.write(index + 1, 1, registration.username, format_row)
            worksheet.write(index + 1, 2,
                            registration.card_number.number if registration.card_number is not None else "", format_row)
            worksheet.write(index + 1, 3, registration.date.strftime("%Y-%m-%d"), format_row)

        workbook.close()
        output_file.seek(0)

        response = HttpResponse(output_file.read(),
                                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

        filename = "MAKE - " + _("Course participants")
        response['Content-Disposition'] = f'attachment; filename="{filename}.xlsx"'

        return response
