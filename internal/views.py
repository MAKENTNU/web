from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, TemplateView, UpdateView

from make_queue.models.course import Printer3DCourse
from util.views import PreventGetRequestsMixin
from .forms import AddMemberForm, EditMemberForm, MemberQuitForm, MemberStatusForm, SecretsForm, ToggleSystemAccessForm
from .models import Member, Secret, SystemAccess


class Home(TemplateView):
    template_name = "internal/home.html"


class SecretsView(ListView):
    model = Secret
    template_name = "internal/secrets.html"
    context_object_name = 'secrets'


class CreateSecretView(PermissionRequiredMixin, CreateView):
    permission_required = 'internal.add_secret'
    model = Secret
    form_class = SecretsForm
    template_name = "internal/secrets_create.html"
    context_object_name = 'secrets'
    success_url = reverse_lazy('secrets')


class EditSecretView(PermissionRequiredMixin, UpdateView):
    permission_required = 'internal.change_secret'
    model = Secret
    form_class = SecretsForm
    template_name = "internal/secrets_edit.html"
    context_object_name = 'secrets'
    success_url = reverse_lazy('secrets')


class DeleteSecretView(PermissionRequiredMixin, PreventGetRequestsMixin, DeleteView):
    permission_required = 'internal.delete_secret'
    model = Secret
    success_url = reverse_lazy('secrets')


class MembersListView(ListView):
    model = Member
    template_name = "internal/members.html"

    def get_context_data(self, *, object_list=None, **kwargs):
        context_data = super().get_context_data(object_list=object_list, **kwargs)
        context_data.update({
            'StatusAction': MemberStatusForm.StatusAction,
        })
        if 'pk' in self.kwargs:
            context_data.update({
                'selected_member': get_object_or_404(Member, pk=self.kwargs['pk']),
            })
        return context_data


class AddMemberView(PermissionRequiredMixin, CreateView):
    permission_required = ('internal.can_register_new_member',)
    model = Member
    form_class = AddMemberForm
    template_name = "internal/add_member.html"

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
    template_name = "internal/edit_member.html"

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


class MemberQuitView(PermissionRequiredMixin, UpdateView):
    permission_required = ('internal.can_edit_group_membership',)
    model = Member
    form_class = MemberQuitForm
    template_name = "internal/member_quit.html"

    def get_success_url(self):
        return reverse('members', args=(self.object.pk,))


class EditMemberStatusView(PermissionRequiredMixin, PreventGetRequestsMixin, UpdateView):
    permission_required = ('internal.can_edit_group_membership',)
    model = Member
    form_class = MemberStatusForm

    def form_invalid(self, form):
        if '__all__' in form.errors:
            for error in form.errors['__all__'].data:
                if error.code == 'warning_message':
                    messages.add_message(self.request, messages.WARNING, error.message)
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('members', args=(self.object.pk,))


class ToggleSystemAccessView(UpdateView):
    model = SystemAccess
    form_class = ToggleSystemAccessForm
    template_name = "internal/system_access_edit.html"

    def get_context_data(self, **kwargs):
        if (self.object.member.user != self.request.user
                and not self.request.user.has_perm('internal.change_systemaccess')):
            raise PermissionDenied("The requesting user does not have permission to change others' system accesses")
        if not self.object.should_be_changed():
            raise Http404("System access should not be changed")
        return super().get_context_data(**kwargs)

    def get_success_url(self):
        return reverse('members', args=(self.object.member.pk,))
