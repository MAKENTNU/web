import io

import xlsxwriter
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView, View, CreateView, UpdateView, DeleteView
from urllib.parse import urlencode

from make_queue.forms import Printer3DCourseForm
from make_queue.models.course import Printer3DCourse


class CourseView(TemplateView):
    template_name = "make_queue/course/course_panel.html"

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data.update({
            "registrations": Printer3DCourse.objects.order_by("name"),
            "possible_statuses": Printer3DCourse.STATUS_CHOICES,
            "message": self.request.GET.get("message", None),
            "type": self.request.GET.get("type", None),
        })
        return context_data


class CreateRegistrationView(PermissionRequiredMixin, CreateView):
    is_next = False
    model = Printer3DCourse
    form_class = Printer3DCourseForm
    template_name = "make_queue/course/registration_create.html"
    permission_required = (
        "make_queue.add_printer3dcourse",
    )

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        if self.is_next:
            context_data["is_next"] = True
        return context_data

    def get_success_url(self):
        return reverse("create_course_registration_success")


class EditRegistrationView(PermissionRequiredMixin, UpdateView):
    model = Printer3DCourse
    form_class = Printer3DCourseForm
    template_name = "make_queue/course/registration_edit.html"
    permission_required = (
        "make_queue.change_printer3dcourse",
    )

    def get_success_url(self):
        return reverse("course_panel")


class DeleteRegistrationView(PermissionRequiredMixin, DeleteView):
    model = Printer3DCourse
    permission_required = (
        "make_queue.delete_printer3dcourse",
    )

    def get_success_url(self):
        return reverse("course_panel")


class BulkStatusUpdate(View):
    """
    Provides a method for bulk updating the status of course registrations
    """

    def post(self, request):
        status = request.POST.get("status")
        registrations = list(map(int, request.POST.getlist("users")))
        Printer3DCourse.objects.filter(pk__in=registrations).update(status=status)

        return redirect("course_panel")


def create_course_registration_xlsx(course_registrations):
    # Use an in-memory output file, to avoid having to clean up the disk
    output_file = io.BytesIO()

    workbook = xlsxwriter.Workbook(output_file, {"in_memory": True})
    worksheet = workbook.add_worksheet("Kursdeltagere")

    # Styles
    format_header = workbook.add_format({
        "bold": True,
        "font_size": 10,
        "font_name": "Arial",
        "font_color": "#000000",
        "bg_color": "#f8c700",
        "border": 1,
        "border_color": "#000000",
    })

    format_row = workbook.add_format({
        "font_size": 10,
        "font_name": "Arial",
        "font_color": "#000000",
        "bg_color": "#fff2cc",
        "border": 1,
        "border_color": "#000000",
    })

    # Set column width
    worksheet.set_column("A:A", 40)
    worksheet.set_column("B:B", 20)
    worksheet.set_column("C:C", 15)
    worksheet.set_column("D:D", 10)

    # Header
    worksheet.write(0, 0, "Navn", format_header)
    worksheet.write(0, 1, "Brukernavn", format_header)
    worksheet.write(0, 2, "Kortnummer", format_header)
    worksheet.write(0, 3, "Dato", format_header)

    for index, registration in enumerate(course_registrations):
        worksheet.write(index + 1, 0, registration.name, format_row)
        worksheet.write(index + 1, 1, registration.username, format_row)
        worksheet.write(index + 1, 2,
                        registration.card_number.number if registration.card_number is not None else "", format_row)
        worksheet.write(index + 1, 3, registration.date.strftime("%Y-%m-%d"), format_row)

    workbook.close()
    output_file.seek(0)
    return output_file


class CourseXLSXView(View):

    def post(self, request):
        search_string = request.POST.get("search_text")
        status_filter = request.POST.get("status_filter")
        selected = request.POST.get("selected")

        # If selected is set, we want to include only these registrations
        if selected:
            course_registrations = Printer3DCourse.objects.filter(pk__in=selected.split(","))
        else:
            course_registrations = Printer3DCourse.objects.filter(
                Q(username__icontains=search_string) | Q(name__icontains=search_string),
                status__icontains=status_filter)

        output_file = create_course_registration_xlsx(course_registrations)
        response = HttpResponse(output_file.read(),
                                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        response['Content-Disposition'] = 'attachment; filename="Kursdeltagere.xlsx"'

        return response


class SendAccessEmailView(View):
    def get(self, request):
        course_registrations = Printer3DCourse.objects.filter(status="registered")
        if course_registrations:
            try:
                file = create_course_registration_xlsx(course_registrations)
                async_to_sync(get_channel_layer().send)(
                    "email", {
                        "type": "send_text",
                        "text": "Nye personer som skal ha tilgang til printerrommet er vedlagt.",
                        "subject": "Tilgang til printerrommet",
                        "from": settings.PRINTER_TEAM_EMAIL,
                        "to": settings.NTNU_ACCESS_CONTROL_EMAIL,
                        "bcc": (settings.PRINTER_TEAM_EMAIL,),
                        "attachments": (
                            (
                                "Kursdeltagere.xlsx",
                                file.read(),
                                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            ),
                        ),
                    }
                )
                course_registrations.update(status="sent")
                params = {"message": _("Email sent"), "type": "positive"}
            except:
                params = {"message": _("Failed to send email."), "type": "negative"}
        else:
            params = {"message": _("No registrations to send"), "type": "warning"}

        return redirect(f"{reverse('course_panel')}?{urlencode(params)}")
