from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin, UserPassesTestMixin
from django.core.exceptions import ValidationError, PermissionDenied
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy, reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView, ListView, CreateView, UpdateView, RedirectView, DeleteView

from internal.forms import AddMemberForm, EditMemberForm, MemberQuitForm, ToggleSystemAccessForm, SecretsForm, EditGuidanceHoursForm
from internal.models import Member, SystemAccess, Secret, GuidanceHours
from make_queue.models.course import Printer3DCourse
from internal.templatetags.guidance_hours import has_reset_guidance_hours_permission


class Home(TemplateView):
    template_name = "internal/home.html"


class GuidanceHoursView(ListView):
    template_name = "internal/guidance_hours.html"
    model = GuidanceHours
    context_object_name = 'guidance_hours'

    def post(self, request):
        for slot in GuidanceHours.objects.all():
            slot.slot_one = None
            slot.slot_two = None
            slot.slot_three = None
            slot.slot_four = None

            slot.save()

        return HttpResponseRedirect(reverse("guidance-hours"))

    def get_queryset(self):
        week_days = {
            'Monday': [],
            'Tuesday': [],
            'Wednesday': [],
            'Thursday': [],
            'Friday': [],
        }

        for slot in GuidanceHours.objects.all():
            week_days.setdefault(slot.day, []).append(slot)

        return week_days

        
class EditGuidanceHoursView(UpdateView):
    template_name = "internal/edit_guidance_hours.html"
    model = GuidanceHours
    form_class = EditGuidanceHoursForm
    success_url = reverse_lazy('guidance-hours')
    context_object_name = 'guidance_hour'


class SecretsView(ListView):
    template_name = "internal/secrets.html"
    model = Secret
    context_object_name = 'secrets'


class CreateSecretView(PermissionRequiredMixin, CreateView):
    template_name = 'internal/secrets_create.html'
    model = Secret
    form_class = SecretsForm
    context_object_name = 'secrets'
    permission_required = 'internal.add_secret'
    success_url = reverse_lazy('secrets')


class EditSecretView(PermissionRequiredMixin, UpdateView):
    template_name = 'internal/secrets_edit.html'
    model = Secret
    form_class = SecretsForm
    context_object_name = 'secrets'
    permission_required = 'internal.change_secret'
    success_url = reverse_lazy('secrets')


class DeleteSecretView(PermissionRequiredMixin, DeleteView):
    model = Secret
    success_url = reverse_lazy('secrets')
    permission_required = 'internal.delete_secret'

    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)


class MembersListView(ListView):
    template_name = "internal/members.html"
    model = Member

    def get_context_data(self, *, object_list=None, **kwargs):
        context_data = super().get_context_data(object_list=object_list, **kwargs)
        if "pk" in self.kwargs:
            context_data.update({
                "selected_member": get_object_or_404(Member, pk=int(self.kwargs["pk"])),
            })
        return context_data


class AddMemberView(PermissionRequiredMixin, CreateView):
    template_name = "internal/add_member.html"
    model = Member
    form_class = AddMemberForm
    permission_required = (
        "internal.can_register_new_member",
    )

    def get_success_url(self):
        return reverse_lazy("edit-member", args=(self.object.pk,))

    def form_valid(self, form):
        user = form.cleaned_data['user']
        registration = Printer3DCourse.objects.filter(username=user.username)
        if registration.exists():
            registration = registration.first()
            user.card_number = registration.card_number
            registration.user = user
            registration.save()
            user.save()
        return super().form_valid(form)


class EditMemberView(UserPassesTestMixin, UpdateView):
    template_name = "internal/edit_member.html"
    model = Member
    form_class = EditMemberForm

    def test_func(self):
        return self.request.user == self.get_object().user or self.request.user.has_perm(
            "internal.can_edit_group_membership")

    def get_form(self, form_class=None):
        if form_class is None:
            form_class = self.get_form_class()
        return form_class(self.request.user, **self.get_form_kwargs())

    def get_success_url(self):
        return reverse("members", args=(self.object.pk,))

    def form_valid(self, form):
        user = self.object.user
        card_number = form.cleaned_data["card_number"]
        user.card_number = card_number
        user.save()
        return super().form_valid(form)


class MemberQuitView(UpdateView):
    template_name = "internal/member_quit.html"
    model = Member
    form_class = MemberQuitForm
    success_url = reverse_lazy("members")

    def form_valid(self, form):
        member = form.instance
        if member.status == 'R' or member.status == 'Q':
            # Fail gracefully
            messages.add_message(self.request, messages.WARNING,
                                 _("Member was not set to quit as the member has already quit or retired."))
        else:
            member.toggle_quit(True, form.cleaned_data["reason_quit"], form.cleaned_data["date_quit"])
            member.save()
        return HttpResponseRedirect(self.get_success_url())


class MemberUndoQuitView(RedirectView):

    def get_redirect_url(self, pk, **kwargs):
        member = get_object_or_404(Member, pk=pk)
        if not member.status == 'R':
            # Fail gracefully
            messages.add_message(self.request, messages.WARNING,
                                 _("Member's quit status was not undone, as the member had not quit."))
        else:
            member.toggle_quit(False)
            member.save()
        return reverse_lazy("members", args=(member.pk,))


class MemberRetireView(RedirectView):

    def get_redirect_url(self, pk, **kwargs):
        member = get_object_or_404(Member, pk=pk)
        if member.status == 'Q' or member.status == 'R':
            # Fail gracefully
            messages.add_message(self.request, messages.WARNING,
                                 _("Member was not set to retired as the member has already quit or retired."))
        else:
            member.toggle_retirement(True)
            member.save()
        return reverse_lazy("members", args=(member.pk,))


class MemberUndoRetireView(RedirectView):

    def get_redirect_url(self, pk, **kwargs):
        member = get_object_or_404(Member, pk=pk)
        if not member.status == 'R':
            # Fail gracefully
            messages.add_message(self.request, messages.WARNING,
                                 _("Member's retirement was not undone, as the member was not retired."))
        else:
            member.toggle_retirement(False)
            member.save()
        return reverse_lazy("members", args=(member.pk,))


class ToggleSystemAccessView(UpdateView):
    template_name = "internal/system_access_edit.html"
    model = SystemAccess
    form_class = ToggleSystemAccessForm

    def get_context_data(self, **kwargs):
        if (self.object.member.user != self.request.user
                and not self.request.user.has_perm("internal.change_systemaccess")):
            raise PermissionDenied("The requesting user does not have permission to change others' system accesses")
        if not self.object.should_be_changed():
            raise Http404("System access should not be changed")
        return super().get_context_data(**kwargs)

    def get_success_url(self):
        return reverse_lazy("members", args=(self.object.member.pk,))
