from abc import ABC

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from contentbox.views import DisplayContentBoxView, EditContentBoxView
from make_queue.models.course import Printer3DCourse
from util.view_utils import CustomFieldsetFormMixin, PreventGetRequestsMixin
from .forms import (
    AddMemberForm, EditMemberForm, MemberQuitForm, MemberRetireForm, MemberStatusForm, QuoteForm, RestrictedEditMemberForm, SecretsForm,
    SystemAccessValueForm,
)
from .models import Member, Quote, Secret, SystemAccess


class InternalDisplayContentBoxView(DisplayContentBoxView):
    extra_context = {
        'base_template': 'internal/base.html',
    }

    change_perms = DisplayContentBoxView.change_perms + ('contentbox.change_internal_contentbox',)


class HomeView(InternalDisplayContentBoxView):
    template_name = 'internal/home.html'


class CommitteeBulletinBoardView(InternalDisplayContentBoxView):
    template_name = 'internal/committee_bulletin_board.html'


class EditInternalContentBoxView(EditContentBoxView):
    permission_required = ('contentbox.change_internal_contentbox',)
    raise_exception = True

    base_template = 'internal/base.html'

    def get_form_kwargs(self):
        return {
            **super().get_form_kwargs(),
            'single_language': settings.LANGUAGE_CODE,
        }


class MemberListView(ListView):
    model = Member
    queryset = Member.objects.select_related('user').prefetch_related('committees__group', 'system_accesses')
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


class MemberFormMixin(CustomFieldsetFormMixin, ABC):
    model = Member

    base_template = 'internal/base.html'
    narrow = False
    centered_title = False
    back_button_text = _("Member list")


class CreateMemberView(PermissionRequiredMixin, MemberFormMixin, CreateView):
    permission_required = ('internal.add_member',)
    form_class = AddMemberForm
    template_name = 'internal/member_add.html'

    form_title = _("Add New Member")
    back_button_link = reverse_lazy('member_list')
    save_button_text = _("Add")
    custom_fieldsets = [
        {'fields': ('user', 'date_joined'), 'layout_class': "ui two fields"},
        {'fields': ('committees',)},
    ]

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


class EditMemberView(PermissionRequiredMixin, MemberFormMixin, UpdateView):

    def has_permission(self):
        return (self.request.user == self.get_object().user
                or self.user_has_edit_perm())

    def user_has_edit_perm(self):
        return self.request.user.has_perm('internal.can_edit_group_membership')

    def get_form_class(self):
        if not self.user_has_edit_perm():
            return RestrictedEditMemberForm
        return EditMemberForm

    def get_form_title(self):
        full_name = self.get_object().user.get_full_name()
        return _("Change Information for {full_name}").format(full_name=full_name)

    def get_back_button_link(self):
        return self.get_success_url()

    def get_custom_fieldsets(self):
        full_form = self.user_has_edit_perm()
        custom_fieldsets = [
            {'fields': ('contact_email', 'phone_number'), 'layout_class': "ui two fields"},
            {'fields': ('google_email', 'MAKE_email' if full_form else None), 'layout_class': "ui two fields"},
            {'fields': ('study_program', 'ntnu_starting_semester'), 'layout_class': "ui two fields"},
            {'fields': ('card_number',), 'layout_class': "ui two fields"},

            {'heading': _("Extra information"), 'icon_class': "info circle"},
            {'fields': ('github_username', 'discord_username'), 'layout_class': "ui two fields"},
            {'fields': ('minecraft_username',), 'layout_class': "ui two fields"},
        ]
        if full_form:
            custom_fieldsets.extend([
                {'heading': _("Membership information"), 'icon_class': "group"},
                {'fields': ('committees', 'role'), 'layout_class': "ui two fields"},
                {'fields': ('comment',)},
                {'fields': ('guidance_exemption', 'active', 'honorary'), 'layout_class': "ui three fields"},
            ])
        return custom_fieldsets

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.object.user:
            kwargs['initial'].update({
                'card_number': self.object.user.card_number,
            })
        return kwargs

    def get_success_url(self):
        return self.object.get_absolute_url()


class MemberRetireView(PermissionRequiredMixin, CustomFieldsetFormMixin, UpdateView):
    permission_required = ('internal.can_edit_group_membership',)
    model = Member
    form_class = MemberRetireForm
    template_name = 'internal/member_retire.html'

    base_template = 'internal/base.html'
    narrow = False
    centered_title = False
    back_button_text = _("Member list")
    save_button_text = _("Set retired")
    custom_fieldsets = [
        {'fields': ('date_quit_or_retired',), 'layout_class': "ui two fields"},
    ]

    def get_form_title(self):
        return _("Set member {name} as retired").format(name=self.object.user.get_full_name())

    def get_back_button_link(self):
        return self.get_success_url()

    def get_success_url(self):
        return self.object.get_absolute_url()


class MemberQuitView(MemberRetireView):
    form_class = MemberQuitForm
    template_name = 'internal/member_quit.html'

    save_button_text = _("Set quit")
    custom_fieldsets = [
        {'fields': ('date_quit_or_retired', 'reason_quit'), 'layout_class': "ui two fields"},
    ]

    def get_form_title(self):
        return _("Set member {name} as quit").format(name=self.object.user.get_full_name())


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
        return self.object.get_absolute_url()


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
        return self.object.member.get_absolute_url()


class SecretListView(ListView):
    model = Secret
    queryset = Secret.objects.default_order_by()
    template_name = 'internal/secret_list.html'
    context_object_name = 'secrets'
    extra_context = {
        'secrets_shown_seconds': 10,
        'secrets_shown_delayed_seconds': 30,
    }


class SecretFormMixin(CustomFieldsetFormMixin, ABC):
    model = Secret
    form_class = SecretsForm
    success_url = reverse_lazy('secret_list')

    base_template = 'internal/base.html'
    back_button_link = success_url
    back_button_text = _("Secrets list")


class CreateSecretView(PermissionRequiredMixin, SecretFormMixin, CreateView):
    permission_required = ('internal.add_secret',)

    form_title = _("New Secret")


class EditSecretView(PermissionRequiredMixin, SecretFormMixin, UpdateView):
    permission_required = ('internal.change_secret',)

    form_title = _("Edit Secret")


class DeleteSecretView(PermissionRequiredMixin, PreventGetRequestsMixin, DeleteView):
    permission_required = ('internal.delete_secret',)
    model = Secret
    success_url = reverse_lazy('secret_list')


class QuoteListView(ListView):
    model = Quote
    template_name = 'internal/quote_list.html'
    context_object_name = 'quotes'
    queryset = Quote.objects.order_by('-date').select_related('author')


class QuoteFormMixin(CustomFieldsetFormMixin, ABC):
    model = Quote
    form_class = QuoteForm
    success_url = reverse_lazy('quote_list')

    base_template = 'internal/base.html'
    back_button_link = success_url
    back_button_text = _("Quotes page")


class QuoteCreateView(PermissionRequiredMixin, QuoteFormMixin, CreateView):
    permission_required = ('internal.add_quote',)
    initial = {
        'date': timezone.localdate,
    }

    form_title = _("New Quote")

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class QuoteUpdateView(PermissionRequiredMixin, QuoteFormMixin, UpdateView):
    form_title = _("Edit Quote")

    def has_permission(self):
        return (
                self.request.user.has_perm('internal.change_quote')
                or self.request.user == self.get_object().author
        )


class QuoteDeleteView(PermissionRequiredMixin, PreventGetRequestsMixin, DeleteView):
    model = Quote
    success_url = reverse_lazy('quote_list')

    def has_permission(self):
        return (
                self.request.user.has_perm('internal.delete_quote')
                or self.request.user == self.get_object().author
        )
