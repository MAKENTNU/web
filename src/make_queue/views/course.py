import io

import xlsxwriter
from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import redirect
from django.template.defaultfilters import capfirst
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.generic import (
    CreateView,
    DeleteView,
    FormView,
    ListView,
    UpdateView,
    View,
)

from make_queue.course_import import ImportResult, import_registrations
from make_queue.forms.course import Printer3DCourseForm, Printer3DCourseImportForm
from make_queue.models.course import Printer3DCourse
from util.view_utils import CustomFieldsetFormMixin, PreventGetRequestsMixin


class Printer3DCourseListView(PermissionRequiredMixin, ListView):
    permission_required = (
        "make_queue.view_printer3dcourse",
        "make_queue.change_printer3dcourse",
    )
    model = Printer3DCourse
    queryset = Printer3DCourse.objects.select_related("user").order_by("name")
    template_name = "make_queue/course/printer_3d_course_list.html"
    context_object_name = "registrations"
    extra_context = {
        "possible_statuses": Printer3DCourse.Status.choices,
    }


class Printer3DCourseCreateView(PermissionRequiredMixin, CreateView):
    permission_required = ("make_queue.add_printer3dcourse",)
    model = Printer3DCourse
    form_class = Printer3DCourseForm
    template_name = "make_queue/course/printer_3d_course_create.html"
    # Redirect back to the same view, to make it easier to create multiple registrations
    success_url = reverse_lazy("printer_3d_course_create")

    def form_valid(self, form):
        messages.success(
            self.request, _("Registration of course participation successful")
        )
        return super().form_valid(form)


class Printer3DCourseImportView(
    PermissionRequiredMixin, CustomFieldsetFormMixin, FormView
):
    permission_required = ("make_queue.add_printer3dcourse",)
    form_class = Printer3DCourseImportForm
    template_name = "make_queue/course/printer_3d_course_import.html"

    narrow = False
    back_button_link = reverse_lazy("printer_3d_course_list")
    back_button_text = _("Course registrations")
    form_title = _("Import Course Registrations")
    save_button_text = _("Import")
    custom_fieldsets = [
        {"fields": ("file",)},
        {"heading": _("Values given to all the imported registrations")},
        {"fields": ("date", "status"), "layout_class": "ui two fields"},
        {"fields": ("course_permissions",)},
        {"heading": _("Options")},
        {"fields": ("skip_already_registered", "import_valid_rows_only")},
    ]

    def get_initial(self):
        return {**super().get_initial(), "date": timezone.localdate()}

    def form_valid(self, form):
        result = import_registrations(
            form.imported_rows,
            default_date=form.cleaned_data["date"],
            status=form.cleaned_data["status"],
            course_permissions=list(form.cleaned_data["course_permissions"]),
            skip_already_registered=form.cleaned_data["skip_already_registered"],
            import_valid_rows_only=form.cleaned_data["import_valid_rows_only"],
        )
        self.add_result_message(result)
        # Render the form again instead of redirecting, to be able to show the outcome
        # of every single row
        return self.render_to_response(
            self.get_context_data(form=form, import_result=result)
        )

    def add_result_message(self, result: ImportResult) -> None:
        counts = {
            "num_created": len(result.created),
            "num_skipped": len(result.skipped),
            "num_failed": len(result.failed),
            "num_read": result.num_read,
        }
        if not result.committed:
            messages.error(
                self.request,
                _(
                    "Nothing was imported, as %(num_failed)d of the %(num_read)d rows"
                    " have errors. Fix the errors and upload the file again, or check"
                    " “Import the valid rows even if some rows have errors”."
                )
                % counts,
            )
        elif result.created:
            messages.success(
                self.request,
                _(
                    "Registered %(num_created)d of the %(num_read)d rows"
                    " (%(num_skipped)d skipped, %(num_failed)d with errors)."
                )
                % counts,
            )
        else:
            messages.warning(
                self.request,
                _(
                    "No registrations were created; all the %(num_read)d rows were"
                    " either skipped or have errors."
                )
                % counts,
            )


class Printer3DCourseUpdateView(PermissionRequiredMixin, UpdateView):
    permission_required = ("make_queue.change_printer3dcourse",)
    model = Printer3DCourse
    form_class = Printer3DCourseForm
    template_name = "make_queue/course/printer_3d_course_form.html"
    success_url = reverse_lazy("printer_3d_course_list")


class Printer3DCourseDeleteView(
    PermissionRequiredMixin, PreventGetRequestsMixin, DeleteView
):
    permission_required = ("make_queue.delete_printer3dcourse",)
    model = Printer3DCourse
    success_url = reverse_lazy("printer_3d_course_list")


class Printer3DCourseStatusBulkUpdateView(PermissionRequiredMixin, View):
    """
    Provides a method for bulk-updating the status of course registrations.
    """

    permission_required = ("make_queue.change_printer3dcourse",)

    def post(self, request):
        status = request.POST.get("status")
        registrations = list(map(int, request.POST.getlist("users")))
        Printer3DCourse.objects.filter(pk__in=registrations).update(status=status)

        return redirect("printer_3d_course_list")


class Printer3DCourseXLSXView(PermissionRequiredMixin, View):
    permission_required = ("make_queue.change_printer3dcourse",)

    def post(self, request):
        search_string = request.POST.get("search_text")
        status_filter = request.POST.get("status_filter")
        selected = request.POST.get("selected")

        # If selected is set, we want to include only these registrations
        if selected:
            course_registrations = Printer3DCourse.objects.filter(
                pk__in=selected.split(",")
            )
        else:
            course_registrations = Printer3DCourse.objects.filter(
                Q(username__icontains=search_string) | Q(name__icontains=search_string),
                status__icontains=status_filter,
            )
        course_registrations = course_registrations.select_related("user")

        # Use an in-memory output file, to avoid having to clean up the disk
        output_file = io.BytesIO()

        workbook = xlsxwriter.Workbook(output_file, {"in_memory": True})
        worksheet = workbook.add_worksheet(str(_("Course participants")))

        # Styles
        format_header = workbook.add_format(
            {
                "bold": True,
                "font_size": 10,
                "font_name": "Arial",
                "font_color": "#000000",
                "bg_color": "#F8C811",
                "border": 1,
                "border_color": "#000000",
            }
        )

        format_row = workbook.add_format(
            {
                "font_size": 10,
                "font_name": "Arial",
                "font_color": "#000000",
                "bg_color": "#FFF2CC",
                "border": 1,
                "border_color": "#000000",
            }
        )

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
            card_number = (
                registration.card_number.number
                if registration.card_number is not None
                else ""
            )
            worksheet.write(index + 1, 2, card_number, format_row)
            worksheet.write(
                index + 1, 3, registration.date.strftime("%Y-%m-%d"), format_row
            )

        workbook.close()
        output_file.seek(0)

        response = HttpResponse(
            output_file.read(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

        filename = "MAKE - " + _("Course participants")
        response["Content-Disposition"] = f'attachment; filename="{filename}.xlsx"'

        return response
