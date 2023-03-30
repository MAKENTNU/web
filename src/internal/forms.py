from django import forms
from django.db import models
from django.utils.translation import gettext_lazy as _

from card import utils as card_utils
from card.formfields import CardNumberField
from users.models import User
from web.widgets import SemanticDateInput, SemanticMultipleSelectInput, SemanticSearchableChoiceInput
from .models import Member, Quote, Secret, SystemAccess


class AddMemberForm(forms.ModelForm):
    class Meta:
        model = Member
        fields = ['user', 'date_joined', 'committees']
        widgets = {
            'user': SemanticSearchableChoiceInput(prompt_text=_("Choose user")),
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
        exclude = ['user', 'date_joined', 'date_quit_or_retired', 'reason_quit', 'quit', 'retired']
        widgets = {
            'comment': forms.TextInput(),
            'committees': SemanticMultipleSelectInput(prompt_text=_("Choose committees")),
        }

    def clean_card_number(self):
        card_number = self.cleaned_data['card_number']
        if card_number:
            if card_utils.is_duplicate(card_number, self.instance.user.username):
                raise forms.ValidationError(_("Card number is already in use"))
        return card_number

    def save(self, commit=True):
        member = super().save(commit=commit)
        user = member.user
        user.card_number = self.cleaned_data['card_number']
        user.save()
        return member


class RestrictedEditMemberForm(EditMemberForm):
    class Meta:
        model = Member
        fields = [
            'contact_email', 'google_email',
            'phone_number',
            'study_program', 'ntnu_starting_semester', 'card_number',
            'github_username', 'discord_username', 'minecraft_username',
        ]


class MemberRetireForm(forms.ModelForm):
    already_quit_or_retired_error_message = _(
        "Member was not set as retired, as the member already has the status “quit” or “retired”."
    )

    class Meta:
        model = Member
        fields = ['date_quit_or_retired']
        widgets = {
            'date_quit_or_retired': SemanticDateInput(),
        }

    def clean(self):
        cleaned_data = super().clean()

        member = self.instance
        if member.retired or member.quit:
            raise forms.ValidationError(
                self.already_quit_or_retired_error_message,
                code='warning_message',
            )
        return cleaned_data

    def save(self, commit=True):
        member = super().save(commit=False)
        # The instance returned by the form's `save()` method contains the cleaned data
        member.set_retirement(True, member.date_quit_or_retired)
        member.save()
        return member


class MemberQuitForm(MemberRetireForm):
    already_quit_or_retired_error_message = _(
        "Member was not set as quit, as the member already has the status “quit” or “retired”."
    )

    class Meta(MemberRetireForm.Meta):
        fields = MemberRetireForm.Meta.fields + ['reason_quit']
        widgets = {
            **MemberRetireForm.Meta.widgets,
            'reason_quit': forms.TextInput(),
        }

    def save(self, commit=True):
        member = super(MemberRetireForm, self).save(commit=False)
        # The instance returned by the form's `save()` method contains the cleaned data
        member.set_quit(True, member.reason_quit, member.date_quit_or_retired)
        member.save()
        return member


class MemberStatusForm(forms.ModelForm):
    class Meta:
        model = Member
        fields = ['status_action']

    class StatusAction(models.TextChoices):
        UNDO_QUIT = 'UQ', "Undo quit"
        UNDO_RETIRE = 'UR', "Undo retire"

    status_action = forms.ChoiceField(choices=StatusAction.choices, required=True)

    def clean(self):
        cleaned_data = super().clean()
        status_action = cleaned_data.get('status_action')
        if not status_action:
            return cleaned_data

        member = self.instance
        match status_action:
            case self.StatusAction.UNDO_QUIT if not member.quit:
                raise forms.ValidationError(
                    _("Member's “quit” status was not undone, as the member did not have the status “quit”."),
                    code='warning_message',
                )
            case self.StatusAction.UNDO_RETIRE if not member.retired:
                raise forms.ValidationError(
                    _("Member's retirement was not undone, as the member did not have the status “retired”."),
                    code='warning_message',
                )
        return cleaned_data

    def save(self, commit=True):
        member = super().save(commit=False)
        status_action = self.cleaned_data['status_action']

        match status_action:
            case self.StatusAction.UNDO_QUIT:
                member.set_quit(False)
            case self.StatusAction.UNDO_RETIRE:
                member.set_retirement(False)
        member.save()
        return member


class SystemAccessValueForm(forms.ModelForm):
    class Meta:
        model = SystemAccess
        fields = ('value',)


class SecretsForm(forms.ModelForm):
    class Meta:
        model = Secret
        fields = '__all__'


class QuoteForm(forms.ModelForm):
    class Meta:
        model = Quote
        fields = ('quote', 'quoted', 'context', 'date')
        widgets = {
            'date': SemanticDateInput(),
        }
