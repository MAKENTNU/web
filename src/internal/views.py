from abc import ABC
from collections import defaultdict
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models.functions import Lower
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.utils.translation import gettext_lazy as _
from django.views.generic import (
    CreateView,
    DeleteView,
    ListView,
    TemplateView,
    UpdateView,
)
from django.views.generic.detail import SingleObjectMixin

from contentbox.views import ContentBoxDetailView, ContentBoxUpdateView
from internal.forms import (
    AddMemberForm,
    ChangeMemberForm,
    MemberQuitForm,
    MemberRetireForm,
    MemberStatusForm,
    QuoteForm,
    RestrictedChangeMemberForm,
    SecretsForm,
    SystemAccessValueForm,
)
from internal.models import Member, Quote, Secret, SystemAccess
from make_queue.models.course import Printer3DCourse
from make_queue.models.machine import Machine, MachineType
from make_queue.models.reservation import Reservation
from util.view_utils import CustomFieldsetFormMixin, PreventGetRequestsMixin


class InternalContentBoxDetailView(ContentBoxDetailView):
    extra_context = {
        "base_template": "internal/base.html",
    }

    change_perms = ContentBoxDetailView.change_perms + (
        "contentbox.change_internal_contentbox",
    )


class HomeView(InternalContentBoxDetailView):
    template_name = "internal/home.html"


def group_by_machine(rows, machines):
    """Pairs each machine with its rows, machines without any rows included."""
    grouped = defaultdict(list)
    for row in rows:
        grouped[row["machine_id"]].append(row)
    return [(machine, grouped[machine.pk]) for machine in machines]


class StatisticsView(TemplateView):
    """Internal statistics page, with a time-range filter for each section."""

    RANGE_PRESETS = {"week": 7, "month": 30, "year": 365}

    template_name = "internal/statistics.html"

    def get_range_for_key(self, key):
        """
        Gets the section's date range, `range_<key>` or
        (`from_<key>` and `to_<key>`).
        """
        params = self.request.GET
        preset = params.get(f"range_{key}")
        now = timezone.now()
        if preset in self.RANGE_PRESETS:
            return now - timedelta(days=self.RANGE_PRESETS[preset]), now
        if preset == "custom":
            f = parse_date(params.get(f"from_{key}") or "")
            t = parse_date(params.get(f"to_{key}") or "")
            tz = timezone.get_current_timezone()
            start = datetime.combine(f, datetime.min.time(), tzinfo=tz) if f else None
            end = datetime.combine(t, datetime.max.time(), tzinfo=tz) if t else None
            return start, end
        return None, None

    def filter_meta(self, key):
        """Returns the filter state that `_stats_filter.html` renders."""
        params = self.request.GET
        return {
            "key": key,
            "range": params.get(f"range_{key}") or "all",
            "date_from": params.get(f"from_{key}", ""),
            "date_to": params.get(f"to_{key}", ""),
            "other_params": self.other_query_params(key),
        }

    def other_query_params(self, key):
        """
        Adds the filter states from the other fields, the one you didn't just change,
        so that the filters don't disappear when adding a filter on another field:)
        """
        own = {f"range_{key}", f"from_{key}", f"to_{key}"}
        return [
            (name, value)
            for name, values in self.request.GET.lists()
            for value in values
            if name not in own
        ]

    def in_date_range(self, queryset, key):
        """Filters a queryset to the date range of the section named by ``key``."""
        start, end = self.get_range_for_key(key)
        if start:
            queryset = queryset.filter(start_time__gte=start)
        if end:
            queryset = queryset.filter(start_time__lte=end)
        return queryset

    def filtered_reservations(self, key, **extra):
        """
        Gets reservations in the date-range, ignores special reservations
        (events, make...)
        """
        return self.in_date_range(
            Reservation.objects.filter(special=False, event__isnull=True, **extra), key
        )

    def get_time_distribution(self):
        """
        Average number of reservations active in each hour of the day.
        """
        counts_per_hour = [0] * 24
        days_seen = set()
        for r in self.filtered_reservations("time").values("start_time", "end_time"):
            start = r["start_time"].replace(minute=0, second=0, microsecond=0)
            end = r["end_time"]
            cur = start
            while cur < end:
                counts_per_hour[cur.hour] += 1
                days_seen.add(cur.date())
                cur += timedelta(hours=1)
        n_days = len(days_seen) or 1
        return {h: round(counts_per_hour[h] / n_days, 2) for h in range(24)}

    def machine_type_section(self, machine_type):
        """
        Hours and number of reservations per machine, returns `None` if the type
        has no machines.
        """
        machines = list(
            Machine.objects.filter(machine_type=machine_type).order_by(Lower("name"))
        )
        if not machines:
            return None

        key = f"mt-{machine_type.pk}"
        rows = self.filtered_reservations(
            key, machine__machine_type=machine_type
        ).values("start_time", "end_time", "machine_id")

        per_machine = [
            {
                "name": machine.name,
                "hours": round(
                    sum(
                        (row["end_time"] - row["start_time"]).total_seconds()
                        for row in machine_rows
                    )
                    / 3600,
                    1,
                ),
                "count": len(machine_rows),
            }
            for machine, machine_rows in group_by_machine(rows, machines)
        ]
        return {
            "name": str(machine_type.name),
            "slug": key,
            "filter": self.filter_meta(key),
            "per_machine": per_machine,
            "reservation_count": sum(m["count"] for m in per_machine),
            "total_hours_sum": round(sum(m["hours"] for m in per_machine), 1),
        }

    def get_machine_type_stats(self):
        """
        Adds a section for each machine type with a sum of the stats in this
        machine type
        """
        sections = (
            self.machine_type_section(machine_type)
            for machine_type in MachineType.objects.order_by("priority")
        )
        return [section for section in sections if section]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "machine_type_groups": self.get_machine_type_stats(),
                "time": self.get_time_distribution(),
                "time_filter": self.filter_meta("time"),
            }
        )
        return context


class CommitteeBulletinBoardView(InternalContentBoxDetailView):
    template_name = "internal/committee_bulletin_board.html"


class InternalContentBoxUpdateView(ContentBoxUpdateView):
    permission_required = ("contentbox.change_internal_contentbox",)
    raise_exception = True

    base_template = "internal/base.html"

    def get_form_kwargs(self):
        return {
            **super().get_form_kwargs(),
            "single_language": settings.LANGUAGE_CODE,
        }


class MemberListView(ListView):
    model = Member
    queryset = Member.objects.select_related("user").prefetch_related(
        "committees__group", "system_accesses"
    )
    template_name = "internal/member_list.html"
    context_object_name = "members"

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        context_data["StatusAction"] = MemberStatusForm.StatusAction
        if pk := self.kwargs.get("pk"):
            context_data["selected_member"] = get_object_or_404(Member, pk=pk)
        return context_data


class MemberFormMixin(CustomFieldsetFormMixin, ABC):
    model = Member

    base_template = "internal/base.html"
    narrow = False
    centered_title = False
    back_button_text = _("Member list")


class MemberCreateView(PermissionRequiredMixin, MemberFormMixin, CreateView):
    permission_required = ("internal.add_member",)
    form_class = AddMemberForm
    template_name = "internal/member_create.html"

    form_title = _("Add New Member")
    back_button_link = reverse_lazy("member_list")
    save_button_text = _("Add")
    custom_fieldsets = [
        {"fields": ("user", "date_joined"), "layout_class": "ui two fields"},
        {"fields": ("committees",)},
    ]

    def get_success_url(self):
        return reverse("member_update", args=(self.object.pk,))

    def form_valid(self, form):
        user = form.cleaned_data["user"]
        registration = Printer3DCourse.objects.filter(username=user.username)
        if registration.exists():
            registration = registration.first()
            user.card_number = registration.card_number
            registration.user = user
            registration.save()
            user.save()
        return super().form_valid(form)


class MemberUpdateView(PermissionRequiredMixin, MemberFormMixin, UpdateView):
    def has_permission(self):
        return self.request.user == self.get_object().user or self.user_has_edit_perm()

    def user_has_edit_perm(self):
        return self.request.user.has_perm("internal.can_edit_group_membership")

    def get_form_class(self):
        if not self.user_has_edit_perm():
            return RestrictedChangeMemberForm
        return ChangeMemberForm

    def get_form_title(self):
        full_name = self.get_object().user.get_full_name()
        return _("Change Information for {full_name}").format(full_name=full_name)

    def get_back_button_link(self):
        return self.get_success_url()

    def get_custom_fieldsets(self):
        full_form = self.user_has_edit_perm()
        return [
            {
                "fields": ("contact_email", "phone_number"),
                "layout_class": "ui two fields",
            },
            {
                "fields": ("google_email", "MAKE_email" if full_form else None),
                "layout_class": "ui two fields",
            },
            {
                "fields": ("study_program", "ntnu_starting_semester"),
                "layout_class": "ui two fields",
            },
            {"fields": ("card_number",), "layout_class": "ui two fields"},
            {"heading": _("Extra information"), "icon_class": "info circle"},
            {
                "fields": ("github_username", "discord_username"),
                "layout_class": "ui two fields",
            },
            {"fields": ("minecraft_username",), "layout_class": "ui two fields"},
            *(
                [
                    {"heading": _("Membership information"), "icon_class": "group"},
                    {"fields": ("committees", "role"), "layout_class": "ui two fields"},
                    {"fields": ("comment",)},
                    {
                        "fields": ("guidance_exemption", "active", "honorary"),
                        "layout_class": "ui three fields",
                    },
                ]
                if full_form
                else []
            ),
        ]

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.object.user:
            kwargs["initial"]["card_number"] = self.object.user.card_number
        return kwargs

    def get_success_url(self):
        return self.object.get_absolute_url()


class MemberRetireView(PermissionRequiredMixin, CustomFieldsetFormMixin, UpdateView):
    permission_required = ("internal.can_edit_group_membership",)
    model = Member
    form_class = MemberRetireForm
    template_name = "internal/member_retire.html"

    base_template = "internal/base.html"
    narrow = False
    centered_title = False
    back_button_text = _("Member list")
    save_button_text = _("Set retired")
    custom_fieldsets = [
        {"fields": ("date_quit_or_retired",), "layout_class": "ui two fields"},
    ]

    def get_form_title(self):
        return _("Set member {name} as retired").format(
            name=self.object.user.get_full_name(),
        )

    def get_back_button_link(self):
        return self.get_success_url()

    def get_success_url(self):
        return self.object.get_absolute_url()


class MemberQuitView(MemberRetireView):
    form_class = MemberQuitForm
    template_name = "internal/member_quit.html"

    save_button_text = _("Set quit")
    custom_fieldsets = [
        {
            "fields": ("date_quit_or_retired", "reason_quit"),
            "layout_class": "ui two fields",
        },
    ]

    def get_form_title(self):
        return _("Set member {name} as quit").format(
            name=self.object.user.get_full_name(),
        )


class MemberStatusUpdateView(
    PermissionRequiredMixin, PreventGetRequestsMixin, UpdateView
):
    permission_required = ("internal.can_edit_group_membership",)
    model = Member
    form_class = MemberStatusForm

    def form_invalid(self, form):
        if "__all__" in form.errors:
            for error in form.errors["__all__"].data:
                if error.code == "warning_message":
                    messages.add_message(self.request, messages.WARNING, error.message)
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return self.object.get_absolute_url()


class SystemAccessUpdateView(
    PermissionRequiredMixin, PreventGetRequestsMixin, UpdateView
):
    model = SystemAccess
    pk_url_kwarg = "system_access_pk"
    form_class = SystemAccessValueForm

    def get_queryset(self):
        return get_object_or_404(Member, pk=self.kwargs["pk"]).system_accesses

    def has_permission(self):
        system_access: SystemAccess = self.get_object()
        return system_access.should_be_changed() and (
            self.request.user == system_access.member.user
            or self.request.user.has_perm("internal.change_systemaccess")
        )

    def get_success_url(self):
        return self.object.member.get_absolute_url()


class SecretListView(ListView):
    model = Secret
    template_name = "internal/secret_list.html"
    context_object_name = "secrets"
    extra_context = {
        "secrets_shown_seconds": 10,
        "secrets_shown_delayed_seconds": 30,
    }

    def get_queryset(self):
        return Secret.objects.visible_to(self.request.user).default_order_by()


class SecretFormMixin(CustomFieldsetFormMixin, ABC):
    model = Secret
    form_class = SecretsForm
    template_name = "internal/secret_form.html"
    success_url = reverse_lazy("secret_list")

    base_template = "internal/base.html"
    back_button_link = success_url
    back_button_text = _("Secrets list")


class SecretCreateView(PermissionRequiredMixin, SecretFormMixin, CreateView):
    permission_required = ("internal.add_secret",)

    form_title = _("Add Secret")
    save_button_text = _("Add")


class ExistingSecretPermissionRequiredMixin(
    PermissionRequiredMixin, SingleObjectMixin, ABC
):
    def get_permission_required(self):
        return self.permission_required + self.get_object().extra_view_perms_str_tuple


class SecretUpdateView(
    ExistingSecretPermissionRequiredMixin, SecretFormMixin, UpdateView
):
    permission_required = ("internal.change_secret",)

    form_title = _("Change Secret")


class SecretDeleteView(
    ExistingSecretPermissionRequiredMixin, PreventGetRequestsMixin, DeleteView
):
    permission_required = ("internal.delete_secret",)
    model = Secret
    success_url = reverse_lazy("secret_list")


class QuoteListView(ListView):
    model = Quote
    template_name = "internal/quote_list.html"
    context_object_name = "quotes"
    queryset = Quote.objects.order_by("-date").select_related("author")


class QuoteFormMixin(CustomFieldsetFormMixin, ABC):
    model = Quote
    form_class = QuoteForm
    success_url = reverse_lazy("quote_list")

    base_template = "internal/base.html"
    back_button_link = success_url
    back_button_text = _("Quotes page")


class QuoteCreateView(PermissionRequiredMixin, QuoteFormMixin, CreateView):
    permission_required = ("internal.add_quote",)
    initial = {
        "date": timezone.localdate,
    }

    form_title = _("Add Quote")
    save_button_text = _("Add")

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class QuoteUpdateView(PermissionRequiredMixin, QuoteFormMixin, UpdateView):
    form_title = _("Change Quote")

    def has_permission(self):
        return (
            self.request.user.has_perm("internal.change_quote")
            or self.request.user == self.get_object().author
        )


class QuoteDeleteView(PermissionRequiredMixin, PreventGetRequestsMixin, DeleteView):
    model = Quote
    success_url = reverse_lazy("quote_list")

    def has_permission(self):
        return (
            self.request.user.has_perm("internal.delete_quote")
            or self.request.user == self.get_object().author
        )
