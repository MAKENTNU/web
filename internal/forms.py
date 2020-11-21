from django import forms
from django.db import models
from django.utils.translation import gettext_lazy as _

from card import utils as card_utils
from card.formfields import CardNumberField
from users.models import User
from web.widgets import SemanticDateInput, SemanticMultipleSelectInput, SemanticSearchableChoiceInput
from .models import Member, Secret, SystemAccess


class AddMemberForm(forms.ModelForm):
    class Meta:
        model = Member
        fields = ['user', 'date_joined', 'committees']
        widgets = {
            'user': SemanticSearchableChoiceInput(prompt_text=_("Choose user"), required=True),
            'date_joined': SemanticDateInput(),
            'committees': SemanticMultipleSelectInput(prompt_text=_("Choose committees")),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['user'].queryset = User.objects.filter(member=None)
        self.fields['user'].label_from_instance = lambda user: user.get_full_name()


class EditMemberForm(forms.ModelForm):
    card_number = CardNumberField(required=False)

    class Meta:
        model = Member
        exclude = ['user', 'date_joined', 'date_quit', 'reason_quit', 'quit', 'retired']
        widgets = {
            'comment': forms.TextInput(),
            'committees': SemanticMultipleSelectInput(prompt_text=_("Choose committees")),
        }

    def __init__(self, user, **kwargs):
        super().__init__(**kwargs)

        member = kwargs['instance']
        if member.user.card_number:
            self.initial['card_number'] = member.user.card_number.number

        if not user.has_perm('internal.can_edit_group_membership'):
            for field_name in ['committees', 'role', 'comment', 'guidance_exemption', 'active', 'honorary']:
                del self.fields[field_name]

    def is_valid(self):
        card_number = self.data['card_number']
        username = self.instance.user.username
        is_duplicate = card_utils.is_duplicate(card_number, username)
        if is_duplicate:
            self.add_error('card_number', _("Card number is already in use"))
        return super().is_valid() and not is_duplicate


class MemberQuitForm(forms.ModelForm):
    class Meta:
        model = Member
        fields = ['date_quit', 'reason_quit']
        widgets = {
            'date_quit': SemanticDateInput(),
            'reason_quit': forms.TextInput(),
        }

    def clean(self):
        cleaned_data = super().clean()

        member = self.instance
        if member.retired or member.quit:
            raise forms.ValidationError(
                _("Member was not set as quit, as the member already has the status “quit” or “retired”."),
                code='warning_message',
            )
        return cleaned_data

    def save(self, commit=True):
        member = super().save(commit=False)
        # The instance returned by the form's `save()` method contains the cleaned data
        member.set_quit(True, member.reason_quit, member.date_quit)
        member.save()
        return member


class MemberStatusForm(forms.ModelForm):
    class Meta:
        model = Member
        fields = ['status_action']

    class StatusAction(models.TextChoices):
        UNDO_QUIT = 'UQ', "Undo quit"
        RETIRE = 'R', "Retire"
        UNDO_RETIRE = 'UR', "Undo retire"

    status_action = forms.ChoiceField(choices=StatusAction.choices, required=True)

    def clean(self):
        cleaned_data = super().clean()
        status_action = cleaned_data.get('status_action')
        if not status_action:
            return cleaned_data

        member = self.instance
        if status_action == self.StatusAction.UNDO_QUIT and not member.quit:
            raise forms.ValidationError(
                _("Member's “quit” status was not undone, as the member did not have the status “quit”."),
                code='warning_message',
            )
        elif status_action == self.StatusAction.RETIRE and (member.quit or member.retired):
            raise forms.ValidationError(
                _("Member was not set as retired, as the member already has the status “quit” or “retired”."),
                code='warning_message',
            )
        elif status_action == self.StatusAction.UNDO_RETIRE and not member.retired:
            raise forms.ValidationError(
                _("Member's retirement was not undone, as the member did not have the status “retired”."),
                code='warning_message',
            )
        return cleaned_data

    def save(self, commit=True):
        member = super().save(commit=False)
        status_action = self.cleaned_data['status_action']

        if status_action == self.StatusAction.UNDO_QUIT:
            member.set_quit(False)
        elif status_action == self.StatusAction.RETIRE:
            member.set_retirement(True)
        elif status_action == self.StatusAction.UNDO_RETIRE:
            member.set_retirement(False)
        member.save()
        return member


class ToggleSystemAccessForm(forms.ModelForm):
    class Meta:
        model = SystemAccess
        fields = '__all__'
        widgets = {
            'name': SemanticSearchableChoiceInput(),
            'member': SemanticSearchableChoiceInput(),
        }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.fields['name'].disabled = True
        self.fields['member'].disabled = True
        self.fields['member'].label_from_instance = lambda member: member.user.get_full_name()


class SecretsForm(forms.ModelForm):
    class Meta:
        model = Secret
        fields = '__all__'
