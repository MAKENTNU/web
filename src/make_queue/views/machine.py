from abc import ABC

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from util.locale_utils import get_current_year_and_week, year_and_week_to_monday
from util.view_utils import (
    CustomFieldsetFormMixin,
    PreventGetRequestsMixin,
    QueryParameterFormMixin,
)
from ..forms.machine import AddMachineForm, ChangeMachineForm, MachineDetailQueryForm
from ..forms.reservation import ReservationListQueryForm
from ..models.machine import Machine, MachineType, MachineUsageRule
from ..models.reservation import Quota
from ..templatetags.reservation_extra import reservation_denied_message


# noinspection PyUnresolvedReferences
class MachineTypeRelatedViewMixin:
    """
    NOTE: When extending this mixin class, it's required to have an ``int`` path converter named ``pk`` as part of the view's path,
    which will be used to query the database for the machine type that the object(s) are related to.
    If found, the machine type will be assigned to a ``machine_type`` field on the view, otherwise, a 404 error will be raised.
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
                # This translation is here instead of in the template, to avoid two translation entries
                # differing only in format syntax (`{var}` vs `%(var)s`)
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
        Create the context required for the controls and the information to be displayed.

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


class MachineDeleteView(PermissionRequiredMixin, PreventGetRequestsMixin, DeleteView):
    permission_required = ("make_queue.delete_machine",)
    model = Machine
    success_url = reverse_lazy("machine_list")


# noinspection PyUnresolvedReferences
class MachineRelatedViewMixin:
    """
    NOTE: When extending this mixin class, it's required to have an ``int`` path converter named ``pk`` as part of the view's path,
    which will be used to query the database for the machine that the object(s) are related to.
    If found, the machine will be assigned to a ``machine`` field on the view, otherwise, a 404 error will be raised.
    """

    machine: Machine

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        machine_pk = self.kwargs["pk"]
        self.machine = get_object_or_404(
            Machine.objects.visible_to(self.request.user), pk=machine_pk
        )
