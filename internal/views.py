from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import ValidationError, PermissionDenied
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy, reverse
from django.views.generic import TemplateView, ListView, CreateView, UpdateView, RedirectView

from internal.forms import AddMemberForm, EditMemberForm, MemberQuitForm, ToggleMemberPropertyForm
from internal.models import Member, MemberProperty


class Home(TemplateView):
    template_name = "internal/home.html"


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


class EditMemberView(UpdateView):
    template_name = "internal/edit_member.html"
    model = Member
    form_class = EditMemberForm

    def get_context_data(self, **kwargs):
        if self.request.user != self.object.user and not self.request.user.has_perm(
                "internal.can_edit_group_membership"):
            raise PermissionDenied(
                "The requesting user does not have access to change the membership information for the given user.")
        return super().get_context_data(**kwargs)

    def get_form(self, form_class=None):
        if form_class is None:
            form_class = self.get_form_class()
        return form_class(self.request.user, **self.get_form_kwargs())

    def get_success_url(self):
        return reverse("members", args=(self.object.pk,))


class MemberQuitView(UpdateView):
    template_name = "internal/member_quit.html"
    model = Member
    form_class = MemberQuitForm
    success_url = reverse_lazy("members")

    def form_valid(self, form):
        member = form.instance
        if member.retired or member.quit:
            raise ValidationError("Bad Request. Tried to set member that is either retired or quit to quit.")
        member.toggle_quit(True, form.cleaned_data["reason_quit"], form.cleaned_data["date_quit"])
        member.save()
        return HttpResponseRedirect(self.get_success_url())


class MemberUndoQuitView(RedirectView):
    def get_redirect_url(self, pk, **kwargs):
        member = get_object_or_404(Member, pk=pk)
        if not member.quit:
            raise ValidationError("Bad Request. Tried to undo quit for a not quit member.")
        member.toggle_quit(False)
        member.save()
        return reverse_lazy("members", args=(member.pk,))


class MemberRetireView(RedirectView):
    def get_redirect_url(self, pk, **kwargs):
        member = get_object_or_404(Member, pk=pk)
        if member.quit or member.retired:
            raise ValidationError("Bad Request. Tried to set member that is either retired or quit to retired.")
        member.toggle_retirement(True)
        member.save()
        return reverse_lazy("members", args=(member.pk,))


class MemberUndoRetireView(RedirectView):
    def get_redirect_url(self, pk, **kwargs):
        member = get_object_or_404(Member, pk=pk)
        if not member.retired:
            raise ValidationError("Bad Request. Tried to undo retirement for a not retired member.")
        member.toggle_retirement(False)
        member.save()
        return reverse_lazy("members", args=(member.pk,))


class ToggleMemberPropertyView(UpdateView):
    template_name = "internal/member_property_edit.html"
    model = MemberProperty
    form_class = ToggleMemberPropertyForm

    def get_context_data(self, **kwargs):
        if self.object.member.user != self.request.user and \
                not self.request.user.has_perm("internal.change_member_property"):
            raise PermissionDenied("The requesting user does not have permission to change other members properties")
        return super().get_context_data(**kwargs)

    def get_success_url(self):
        return reverse_lazy("members", args=(self.object.member.pk,))
