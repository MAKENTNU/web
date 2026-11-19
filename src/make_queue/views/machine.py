from abc import ABC

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    FormView,
    ListView,
    UpdateView,
)

from make_queue import printer_api
from make_queue.forms.machine import (
    AddMachineForm,
    ChangeMachineForm,
    GcodeUploadForm,
    MachineDetailQueryForm,
)
from make_queue.forms.reservation import ReservationListQueryForm
from make_queue.models.machine import Machine, MachineType, MachineUsageRule
from make_queue.models.reservation import Quota
from make_queue.templatetags.reservation_extra import reservation_denied_message
from util.locale_utils import get_current_year_and_week, year_and_week_to_monday
from util.logging_utils import get_request_logger
from util.view_utils import (
    CustomFieldsetFormMixin,
    PreventGetRequestsMixin,
    QueryParameterFormMixin,
)


# noinspection PyUnresolvedReferences
class MachineTypeRelatedViewMixin:
    """
    NOTE: When extending this mixin class, it's required to have an ``int`` path
          converter named ``pk`` as part of the view's path, which will be used to query
          the database for the machine type that the object(s) are related to.
          If found, the machine type will be assigned to a ``machine_type`` field on
          the view, otherwise, a 404 error will be raised.
    """

    machine_type: MachineType

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        machine_type_pk = self.kwargs["pk"]
        self.machine_type = get_object_or_404(MachineType, pk=machine_type_pk)

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            **{
                "machine_type": self.machine_type,
                **kwargs,
            }
        )


class MachineUsageRuleDetailView(MachineTypeRelatedViewMixin, DetailView):
    model = MachineUsageRule
    template_name = "make_queue/machine_usage_rule_detail.html"
    context_object_name = "usage_rules"

    def get_object(self, queryset=None):
        usage_rule, _created = MachineUsageRule.objects.get_or_create(
            machine_type=self.machine_type
        )
        return usage_rule

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            **{
                # This translation is here instead of in the template, to avoid two
                # translation entries differing only in format syntax
                # (`{var}` vs `%(var)s`)
                "title": _("Usage rules for {machine_type}").format(
                    machine_type=self.machine_type,
                ),
                **kwargs,
            }
        )


class MachineUsageRuleUpdateView(
    PermissionRequiredMixin,
    CustomFieldsetFormMixin,
    MachineTypeRelatedViewMixin,
    UpdateView,
):
    permission_required = ("make_queue.change_machineusagerule",)
    model = MachineUsageRule
    fields = ("content",)
    template_name = "make_queue/machine_usage_rule_form.html"

    narrow = False

    def get_object(self, queryset=None):
        return self.machine_type.usage_rule

    def get_form_title(self):
        return _("Change Usage Rules for {machine_type}").format(
            machine_type=self.machine_type,
        )

    def get_back_button_link(self):
        return self.get_success_url()

    def get_back_button_text(self):
        return _("View usage rules for {machine_type}").format(
            machine_type=self.machine_type,
        )

    def get_success_url(self):
        return self.get_object().get_absolute_url()


class MachineListView(ListView):
    """View that shows all the machines -- listed per machine type."""

    model = MachineType
    template_name = "make_queue/machine_list.html"
    context_object_name = "machine_types"
    extra_context = {
        "ReservationOwner": ReservationListQueryForm.Owner,
    }

    def get_queryset(self):
        machine_queryset = Machine.objects.visible_to(
            self.request.user
        ).default_order_by()
        return MachineType.objects.default_order_by().prefetch_machines(
            machine_queryset=machine_queryset,
            machines_attr_name="shown_machines",
        )


class MachineDetailView(QueryParameterFormMixin, DetailView):
    """Main view for showing the reservation calendar for a machine."""

    model = Machine
    form_class = MachineDetailQueryForm
    template_name = "make_queue/machine_detail.html"
    context_object_name = "machine"
    extra_context = {
        "ReservationOwner": ReservationListQueryForm.Owner,
    }

    def get_queryset(self):
        return Machine.objects.visible_to(self.request.user)

    def get_context_data(self, **kwargs):
        """
        Create the context required for the controls and the information to be
        displayed.

        :return: context required to show the reservation calendar with controls
        """
        machine: Machine = self.object
        if self.request.GET:
            selected_year, selected_week = (
                self.query_params["calendar_year"],
                self.query_params["calendar_week"],
            )
        else:
            selected_year, selected_week = get_current_year_and_week()

        context = {
            **super().get_context_data(**kwargs),
            "reservation_denied_message": reservation_denied_message(
                self.request.user, machine
            ),
            "can_ignore_rules": False,
            "other_machines": (
                Machine.objects.exclude(pk=machine.pk)
                .filter(machine_type=machine.machine_type)
                .visible_to(self.request.user)
                .default_order_by()
            ),
            "selected_year": selected_year,
            "selected_week": selected_week,
            "selected_date": year_and_week_to_monday(selected_year, selected_week),
            "can_upload_gcode": machine.can_user_upload_gcode(self.request.user),
        }

        if self.request.user.is_authenticated:
            context["can_ignore_rules"] = any(
                quota.can_create_more_reservations(self.request.user)
                for quota in Quota.get_user_quotas(
                    self.request.user, machine.machine_type
                ).filter(ignore_rules=True)
            )

        return context


class MachineFormMixin(CustomFieldsetFormMixin, ABC):
    model = Machine
    success_url = reverse_lazy("machine_list")

    narrow = False
    back_button_link = success_url
    back_button_text = _("Machine list")

    should_include_machine_type: bool

    def get_custom_fieldsets(self):
        return [
            {
                "fields": (
                    "machine_type" if self.should_include_machine_type else None,
                    "machine_model",
                ),
                "layout_class": "ui two fields",
            },
            {"fields": ("name",), "layout_class": "ui two fields"},
            {"fields": ("stream_name",), "layout_class": "ui two fields"}
            if self.should_include_stream_name()
            else None,
            {"fields": ("printer_address",), "layout_class": "ui two fields"}
            if self.should_include_printer_address()
            else None,
            {"fields": ("location", "location_url"), "layout_class": "ui two fields"},
            {"fields": ("priority", "status"), "layout_class": "ui two fields"},
            {
                "fields": ("info_message", "info_message_date"),
                "layout_class": "ui two fields",
            },
            {"fields": ("internal",), "layout_class": "ui segment field"},
            {"fields": ("notes",)},
        ]

    def should_include_stream_name(self):
        return True

    def should_include_printer_address(self):
        return True


class MachineCreateView(PermissionRequiredMixin, MachineFormMixin, CreateView):
    permission_required = ("make_queue.add_machine",)
    form_class = AddMachineForm

    form_title = _("Add Machine")
    save_button_text = _("Add")

    should_include_machine_type = True


class MachineUpdateView(PermissionRequiredMixin, MachineFormMixin, UpdateView):
    permission_required = ("make_queue.change_machine",)
    form_class = ChangeMachineForm

    form_title = _("Change Machine")

    should_include_machine_type = False

    def should_include_stream_name(self):
        return self.object.machine_type.has_stream

    def should_include_printer_address(self):
        return self.object.machine_type.has_ip


class MachineDeleteView(PermissionRequiredMixin, PreventGetRequestsMixin, DeleteView):
    permission_required = ("make_queue.delete_machine",)
    model = Machine
    success_url = reverse_lazy("machine_list")


# noinspection PyUnresolvedReferences
class MachineRelatedViewMixin:
    """
    NOTE: When extending this mixin class, it's required to have an ``int`` path
          converter named ``pk`` as part of the view's path, which will be used to query
          the database for the machine that the object(s) are related to.
          If found, the machine will be assigned to a ``machine`` field on the view,
          otherwise, a 404 error will be raised.
    """

    machine: Machine

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        machine_pk = self.kwargs["pk"]
        self.machine = get_object_or_404(
            Machine.objects.visible_to(self.request.user), pk=machine_pk
        )


class GcodeUploadView(
    LoginRequiredMixin, MachineRelatedViewMixin, CustomFieldsetFormMixin, FormView
):
    """Lets users upload G-code files directly to a 3D printer (see ``printer_api``)."""

    form_class = GcodeUploadForm
    template_name = "make_queue/gcode_upload_form.html"

    save_button_text = _("Upload")
    cancel_button = False

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not self.machine.can_user_upload_gcode(
            request.user
        ):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_form_title(self):
        return _("Upload G-code to %(machine)s") % {"machine": self.machine.name}

    def get_back_button_link(self):
        return self.machine.get_absolute_url()

    def get_back_button_text(self):
        return self.machine.name

    def get_success_url(self):
        # Show the form again, to make it easy to upload another file
        return self.request.path

    def get_context_data(self, **kwargs):
        print_state = printer_api.get_print_state(self.machine.printer_address)
        return {
            **super().get_context_data(**kwargs),
            "print_state": print_state,
            "printer_is_offline": print_state == printer_api.OFFLINE_STATE,
            "printer_is_busy": print_state in printer_api.BUSY_PRINT_STATES,
        }

    def form_valid(self, form):
        address = self.machine.printer_address
        print_state = printer_api.get_print_state(address)
        if print_state == printer_api.OFFLINE_STATE:
            form.add_error(None, _("The printer is offline."))
            return self.form_invalid(form)
        if print_state in printer_api.BUSY_PRINT_STATES:
            form.add_error(
                None, _("Files can't be uploaded while the printer is printing.")
            )
            return self.form_invalid(form)

        file = form.cleaned_data["file"]
        filename = file.name
        # Makes it easy to see on the printer who uploaded which file
        username = self.request.user.username
        if username.lower() not in filename.lower():
            filename = f"{username}-{filename}"

        try:
            printer_api.upload_gcode(address, file, filename=filename)
        except printer_api.PrinterError as e:
            get_request_logger().warning(
                "Uploading G-code to %s failed",
                self.machine,
                exc_info=e,
                extra={"request": self.request},
            )
            form.add_error(None, e.user_message)
            return self.form_invalid(form)

        messages.success(
            self.request,
            _("“%(filename)s” was uploaded to %(machine)s.")
            % {"filename": filename, "machine": self.machine.name},
        )
        return super().form_valid(form)
