import io

import xlsxwriter
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Case, Q, When
from django.http import HttpResponse
from django.shortcuts import redirect
from django.template.defaultfilters import capfirst
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, DeleteView, ListView, UpdateView, View
from django.views.generic.detail import SingleObjectMixin

from card import utils as card_utils
from make_queue.forms.course import (
    CourseRegistrationRequestForm,
    Printer3DCourseForm,
)
from make_queue.models.course import (
    CoursePermission,
    CourseRegistrationConfirmation,
    CourseRegistrationRequest,
    Printer3DCourse,
)
from util.view_utils import PreventGetRequestsMixin


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

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            "num_pending_requests": CourseRegistrationRequest.objects.filter(
                status=CourseRegistrationRequest.Status.PENDING
            ).count(),
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


class CourseRegistrationRequestCreateView(LoginRequiredMixin, CreateView):
    """
    Lets a logged-in user ask to be registered as having taken the 3D printer course.

    The request does not grant any access on its own; someone with the permission to
    add course registrations has to approve it first.
    """

    model = CourseRegistrationRequest
    form_class = CourseRegistrationRequestForm
    template_name = "make_queue/course/course_registration_request_form.html"
    success_url = reverse_lazy("course_registration_request_create")

    def get_form_kwargs(self):
        return {**super().get_form_kwargs(), "user": self.request.user}

    def get_initial(self):
        return {**super().get_initial(), "course_date": timezone.localdate()}

    def get_existing_registration(self) -> Printer3DCourse | None:
        return Printer3DCourse.objects.filter(
            Q(user=self.request.user) | Q(username=self.request.user.username)
        ).first()

    def get_pending_request(self) -> CourseRegistrationRequest | None:
        return self.request.user.course_registration_requests.filter(
            status=CourseRegistrationRequest.Status.PENDING
        ).first()

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            "existing_registration": self.get_existing_registration(),
            "pending_request": self.get_pending_request(),
        }

    def form_valid(self, form):
        # Guard against a second request being submitted from a stale page
        if self.get_existing_registration() or self.get_pending_request():
            messages.error(self.request, _("You have already submitted a request."))
            return redirect(self.success_url)

        messages.success(
            self.request,
            _(
                "Your request has been submitted, and will show up here once it has"
                " been approved."
            ),
        )
        return super().form_valid(form)


class CourseRegistrationRequestListView(PermissionRequiredMixin, ListView):
    permission_required = ("make_queue.add_printer3dcourse",)
    model = CourseRegistrationRequest
    queryset = (
        CourseRegistrationRequest.objects.select_related("user")
        .prefetch_related("confirmations")
        .order_by(
            # Show the requests that need to be handled first
            Case(
                When(status=CourseRegistrationRequest.Status.PENDING, then=0), default=1
            ),
            "submitted",
        )
    )
    template_name = "make_queue/course/course_registration_request_list.html"
    context_object_name = "registration_requests"

    def get_context_data(self, **kwargs):
        return {
            **super().get_context_data(**kwargs),
            "num_active_confirmations": CourseRegistrationConfirmation.objects.filter(
                active=True
            ).count(),
            "course_permissions": CoursePermission.objects.exclude(
                short_name__in=(
                    CoursePermission.DefaultPerms.IS_AUTHENTICATED,
                    CoursePermission.DefaultPerms.TAKEN_3D_PRINTER_COURSE,
                )
            ).order_by("name"),
        }


class CourseRegistrationRequestApproveView(
    PermissionRequiredMixin, PreventGetRequestsMixin, SingleObjectMixin, View
):
    permission_required = ("make_queue.add_printer3dcourse",)
    model = CourseRegistrationRequest

    def post(self, request, *args, **kwargs):
        registration_request = self.get_object()
        if registration_request.status != CourseRegistrationRequest.Status.PENDING:
            messages.error(request, _("The request has already been handled."))
            return redirect("course_registration_request_list")

        card_number = registration_request.card_number
        username = registration_request.user.username
        if card_number and card_utils.is_duplicate(card_number, username):
            messages.error(
                request,
                _("The card number of %(user)s is already in use by someone else.")
                % {"user": registration_request.user},
            )
            return redirect("course_registration_request_list")

        course_permissions = CoursePermission.objects.filter(
            pk__in=request.POST.getlist("course_permissions")
        )
        registration_request.approve(course_permissions)
        messages.success(
            request,
            _("%(user)s was registered as having taken the course.")
            % {"user": registration_request.user},
        )
        return redirect("course_registration_request_list")


class CourseRegistrationRequestRejectView(
    PermissionRequiredMixin, PreventGetRequestsMixin, SingleObjectMixin, View
):
    permission_required = ("make_queue.add_printer3dcourse",)
    model = CourseRegistrationRequest

    def post(self, request, *args, **kwargs):
        registration_request = self.get_object()
        registration_request.reject()
        messages.success(
            request,
            _("The request from %(user)s was rejected.")
            % {"user": registration_request.user},
        )
        return redirect("course_registration_request_list")
