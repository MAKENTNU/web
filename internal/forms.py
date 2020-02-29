from django.forms import ModelForm, TextInput
from django.utils.translation import gettext_lazy as _

import card.utils
from card.forms import CardNumberField
from internal.models import Member, SystemAccess
from users.models import User
from web.widgets import SemanticSearchableChoiceInput, SemanticDateInput, SemanticMultipleSelectInput


class AddMemberForm(ModelForm):
    class Meta:
        model = Member
        fields = ["user", "date_joined", "committees"]
        widgets = {
            "user": SemanticSearchableChoiceInput(prompt_text=_("Choose user"), required=True),
            "date_joined": SemanticDateInput(),
            "committees": SemanticMultipleSelectInput(prompt_text=_("Choose committees")),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["user"].queryset = User.objects.filter(member=None)
        self.fields["user"].label_from_instance = lambda user: user.get_full_name()


class EditMemberForm(ModelForm):
    card_number = CardNumberField(required=False)

    class Meta:
        model = Member
        fields = "__all__"
        exclude = ["user", "date_joined", "date_quit", "quit", "reason_quit", "retired"]

        widgets = {
            "comment": TextInput(),
            "committees": SemanticMultipleSelectInput(prompt_text=_("Choose committees")),
        }

    def __init__(self, user, **kwargs):
        super().__init__(**kwargs)

        member = kwargs['instance']
        if member.user.card_number:
            self.initial['card_number'] = member.user.card_number.number

        if not user.has_perm("internal.can_edit_group_membership"):
            for field_name in ["committees", "role", "comment", "guidance_exemption", "active", "honorary"]:
                del self.fields[field_name]

    def is_valid(self):
        card_number = self.data["card_number"]
        username = self.instance.user.username
        is_duplicate = card.utils.is_duplicate(card_number, username)
        if is_duplicate:
            self.add_error("card_number", _("Card number is already in use"))
        return super().is_valid() and not is_duplicate


class MemberQuitForm(ModelForm):
    class Meta:
        model = Member
        fields = ["date_quit", "reason_quit"]

        widgets = {
            "date_quit": SemanticDateInput(),
            "reason_quit": TextInput(),
        }


class ToggleSystemAccessForm(ModelForm):
    class Meta:
        model = SystemAccess
        fields = "__all__"

        widgets = {
            "name": SemanticSearchableChoiceInput(),
            "member": SemanticSearchableChoiceInput(),
        }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.fields["name"].disabled = True
        self.fields["member"].disabled = True
        self.fields["member"].label_from_instance = lambda member: member.user.get_full_name()
