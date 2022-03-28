from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, TemplateView, UpdateView

from make_queue.models.course import Printer3DCourse
from util.view_utils import PreventGetRequestsMixin
from .forms import AddMemberForm, EditMemberForm, MemberQuitForm, MemberStatusForm, RestrictedEditMemberForm, \
    SecretsForm, SystemAccessValueForm, QuoteForm
from .models import Member, Secret, SystemAccess, Quote


class HomeView(TemplateView):
    template_name = 'internal/home.html'


class QuoteListView(ListView):
    model = Quote
    template_name = 'internal/quotes_list.html'
    context_object_name = 'quotes'
    queryset = Quote.objects.order_by('-pk')


class CreateQuoteView(PermissionRequiredMixin, CreateView):
    permission_required = ('internal.add_quote',)
    model = Quote
    form_class = QuoteForm
    template_name = 'internal/quote_create.html'
    context_object_name = 'quote'
    success_url = reverse_lazy('quotes_list')

    def form_valid(self, form, **kwargs):
        form.instance.author = self.request.user
        return super().form_valid(form)


class EditQuoteView(PermissionRequiredMixin, UpdateView):
    permission_required = ('internal.change_quote',)
    model = Quote
    form_class = QuoteForm
    template_name = 'internal/quote_edit.html'
    context_object_name = 'quote'
    success_url = reverse_lazy('quotes_list')


class DeleteQuoteView(PermissionRequiredMixin, PreventGetRequestsMixin, DeleteView):
    permission_required = ('internal.delete_quote',)
    model = Quote
    success_url = reverse_lazy('quotes_list')


class SecretListView(ListView):
    model = Secret
    queryset = Secret.objects.default_order_by()
    template_name = 'internal/secret_list.html'
    context_object_name = 'secrets'


class CreateSecretView(PermissionRequiredMixin, CreateView):
    permission_required = ('internal.add_secret',)
    model = Secret
    form_class = SecretsForm
    template_name = 'internal/secret_create.html'
    context_object_name = 'secrets'
    success_url = reverse_lazy('secret_list')


class EditSecretView(PermissionRequiredMixin, UpdateView):
    permission_required = ('internal.change_secret',)
    model = Secret
    form_class = SecretsForm
    template_name = 'internal/secret_edit.html'
    context_object_name = 'secrets'
    success_url = reverse_lazy('secret_list')


class DeleteSecretView(PermissionRequiredMixin, PreventGetRequestsMixin, DeleteView):
    permission_required = ('internal.delete_secret',)
    model = Secret
    success_url = reverse_lazy('secret_list')


class MemberListView(ListView):
    model = Member
    template_name = 'internal/member_list.html'
    context_object_name = 'members'

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data.update({
            'StatusAction': MemberStatusForm.StatusAction,
        })
        if 'pk' in self.kwargs:
            context_data.update({
                'selected_member': get_object_or_404(Member, pk=self.kwargs['pk']),
            })
        return context_data


class CreateMemberView(PermissionRequiredMixin, CreateView):
    permission_required = ('internal.can_register_new_member',)
    model = Member
    form_class = AddMemberForm
    template_name = 'internal/member_create.html'

    def get_success_url(self):
        return reverse('edit_member', args=(self.object.pk,))

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
    template_name = 'internal/member_edit.html'

    def has_permission(self):
        return (self.request.user == self.get_object().user
                or self.request.user.has_perm('internal.can_edit_group_membership'))

    def get_form_class(self):
        if not self.request.user.has_perm('internal.can_edit_group_membership'):
            return RestrictedEditMemberForm
        return EditMemberForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.object.user:
            kwargs['initial'].update({
                'card_number': self.object.user.card_number,
            })
        return kwargs

    def get_success_url(self):
        return reverse('member_list', args=(self.object.pk,))


class MemberQuitView(PermissionRequiredMixin, UpdateView):
    permission_required = ('internal.can_edit_group_membership',)
    model = Member
    form_class = MemberQuitForm
    template_name = 'internal/member_quit.html'

    def get_success_url(self):
        return reverse('member_list', args=(self.object.pk,))


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
        return reverse('member_list', args=(self.object.pk,))


class EditSystemAccessView(PermissionRequiredMixin, PreventGetRequestsMixin, UpdateView):
    model = SystemAccess
    form_class = SystemAccessValueForm

    def get_queryset(self):
        return get_object_or_404(Member, pk=self.kwargs['member_pk']).system_accesses

    def has_permission(self):
        system_access: SystemAccess = self.get_object()
        return (
                system_access.should_be_changed()
                and (self.request.user == system_access.member.user
                     or self.request.user.has_perm('internal.change_systemaccess'))
        )

    def get_success_url(self):
        return reverse('member_list', args=(self.object.member.pk,))
