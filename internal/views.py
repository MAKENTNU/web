from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, DeleteView, ListView, RedirectView, TemplateView, UpdateView

from make_queue.models.course import Printer3DCourse
from .forms import AddMemberForm, EditMemberForm, MemberQuitForm, SecretsForm, ToggleSystemAccessForm
from .models import Member, Secret, SystemAccess


class HomeView(TemplateView):
    template_name = 'internal/home.html'


class SecretsView(ListView):
    model = Secret
    template_name = 'internal/secret_list.html'
    context_object_name = 'secrets'


class CreateSecretView(PermissionRequiredMixin, CreateView):
    permission_required = ('internal.add_secret',)
    model = Secret
    form_class = SecretsForm
    template_name = 'internal/secret_create.html'
    context_object_name = 'secrets'
    success_url = reverse_lazy('secrets')


class EditSecretView(PermissionRequiredMixin, UpdateView):
    permission_required = ('internal.change_secret',)
    model = Secret
    form_class = SecretsForm
    template_name = 'internal/secret_edit.html'
    context_object_name = 'secrets'
    success_url = reverse_lazy('secrets')


class DeleteSecretView(PermissionRequiredMixin, DeleteView):
    permission_required = ('internal.delete_secret',)
    model = Secret
    success_url = reverse_lazy('secrets')


class MembersListView(ListView):
    model = Member
    template_name = 'internal/member_list.html'

    def get_context_data(self, *, object_list=None, **kwargs):
        context_data = super().get_context_data(object_list=object_list, **kwargs)
        if 'pk' in self.kwargs:
            context_data.update({
                'selected_member': get_object_or_404(Member, pk=self.kwargs['pk']),
            })
        return context_data


class AddMemberView(PermissionRequiredMixin, CreateView):
    permission_required = ('internal.can_register_new_member',)
    model = Member
    form_class = AddMemberForm
    template_name = 'internal/member_create.html'

    def get_success_url(self):
        return reverse('edit-member', args=(self.object.pk,))

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


class EditMemberView(PermissionRequiredMixin, UpdateView):
    model = Member
    form_class = EditMemberForm
    template_name = 'internal/member_edit.html'

    def has_permission(self):
        return (self.request.user == self.get_object().user
                or self.request.user.has_perm('internal.can_edit_group_membership'))

    def get_form(self, form_class=None):
        if form_class is None:
            form_class = self.get_form_class()
        return form_class(self.request.user, **self.get_form_kwargs())

    def get_success_url(self):
        return reverse('members', args=(self.object.pk,))

    def form_valid(self, form):
        user = self.object.user
        card_number = form.cleaned_data['card_number']
        user.card_number = card_number
        user.save()
        return super().form_valid(form)


class MemberQuitView(UpdateView):
    model = Member
    form_class = MemberQuitForm
    template_name = 'internal/member_quit.html'
    success_url = reverse_lazy('members')

    def form_valid(self, form):
        member = form.instance
        if member.retired or member.quit:
            # Fail gracefully
            messages.add_message(
                self.request, messages.WARNING,
                _("Member was not set to quit as the member has already quit or retired."),
            )
        else:
            member.set_quit(True, form.cleaned_data['reason_quit'], form.cleaned_data['date_quit'])
            member.save()
        return HttpResponseRedirect(self.get_success_url())


class MemberUndoQuitView(RedirectView):

    def get_redirect_url(self, pk, **kwargs):
        member = get_object_or_404(Member, pk=pk)
        if not member.quit:
            # Fail gracefully
            messages.add_message(
                self.request, messages.WARNING,
                _("Member's quit status was not undone, as the member had not quit."),
            )
        else:
            member.set_quit(False)
            member.save()
        return reverse_lazy('members', args=(member.pk,))


class MemberRetireView(RedirectView):

    def get_redirect_url(self, pk, **kwargs):
        member = get_object_or_404(Member, pk=pk)
        if member.quit or member.retired:
            # Fail gracefully
            messages.add_message(
                self.request, messages.WARNING,
                _("Member was not set to retired as the member has already quit or retired."),
            )
        else:
            member.set_retirement(True)
            member.save()
        return reverse_lazy('members', args=(member.pk,))


class MemberUndoRetireView(RedirectView):

    def get_redirect_url(self, pk, **kwargs):
        member = get_object_or_404(Member, pk=pk)
        if not member.retired:
            # Fail gracefully
            messages.add_message(
                self.request, messages.WARNING,
                _("Member's retirement was not undone, as the member was not retired."),
            )
        else:
            member.set_retirement(False)
            member.save()
        return reverse_lazy('members', args=(member.pk,))


class ToggleSystemAccessView(UpdateView):
    model = SystemAccess
    form_class = ToggleSystemAccessForm
    template_name = 'internal/system_access_edit.html'

    def get_context_data(self, **kwargs):
        if (self.object.member.user != self.request.user
                and not self.request.user.has_perm('internal.change_systemaccess')):
            raise PermissionDenied("The requesting user does not have permission to change others' system accesses")
        if not self.object.should_be_changed():
            raise Http404("System access should not be changed")
        return super().get_context_data(**kwargs)

    def get_success_url(self):
        return reverse('members', args=(self.object.member.pk,))
