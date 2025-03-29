from django import forms
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from card import utils as card_utils
from card.formfields import CardNumberField
from users.models import User
from web.widgets import SemanticChoiceInput, SemanticDateInput, SemanticSearchableChoiceInput
from ..models.course import CoursePermission, Printer3DCourse


class Printer3DCourseForm(forms.ModelForm):
    card_number = CardNumberField(required=False)

    class Meta:
        model = Printer3DCourse
        exclude = ['_card_number']
        widgets = {
            'status': SemanticChoiceInput(),
            'date': SemanticDateInput(),
            'username': forms.TextInput(attrs={'autofocus': 'autofocus'}),
            'course_permissions': forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)
        if self.instance.user:
            queryset = User.objects.filter(Q(printer_3d_course=self.instance))
        else:
            queryset = User.objects.filter(Q(printer_3d_course=None))
        self.fields['user'] = forms.ModelChoiceField(
            queryset=queryset,
            required=False,
            widget=SemanticSearchableChoiceInput(prompt_text=_("Select user")),
            label=Printer3DCourse._meta.get_field('user').verbose_name,
        )
        if self.instance.card_number is not None:
            self.initial['card_number'] = self.instance.card_number

        self.fields['course_permissions'].queryset = self.fields['course_permissions'].queryset.exclude(short_name='AUTH').exclude(short_name='3DPR').order_by('name')
        self.fields['course_permissions'].widget.attrs['class'] = 'ui fluid checkbox'

        self.base_permission = CoursePermission.objects.get(short_name='3DPR')



    def clean_card_number(self):
        card_number: str = self.cleaned_data['card_number']
        if card_number:
            # This accident prevention was requested by the Mentor committee.
            # Phone number is from https://i.ntnu.no/wiki/-/wiki/Norsk/Vakt+og+service+p%C3%A5+campus
            if card_number.lstrip("0") == "91897373":
                raise forms.ValidationError(
                    # Translators: See the Norwegian and English versions of this page for
                    # a translation of "Building security":
                    # https://i.ntnu.no/wiki/-/wiki/Norsk/Vakt+og+service+p%C3%A5+campus
                    _("The card number was detected to be the phone number of Building security at NTNU. Please enter a valid card number.")
                )
        return card_number
    
    def clean_course_permissions(self):
        course_permissions = set(self.cleaned_data['course_permissions'])    
        course_permissions.add(self.base_permission)
        return list(course_permissions)

    def clean(self):
        cleaned_data = super().clean()
        card_number = cleaned_data.get('card_number')
        username = cleaned_data.get('username')        

        if card_number and username:
            if card_utils.is_duplicate(card_number, username):
                raise forms.ValidationError({
                    'card_number': _("Card number is already in use"),
                })
        return cleaned_data

    def save(self, commit=True):
        course = super().save(commit=False)
        course.card_number = self.cleaned_data['card_number']
        course.save()
        course.course_permissions.set(self.cleaned_data['course_permissions'])

        return course
