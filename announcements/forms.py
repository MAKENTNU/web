from django.forms import ModelForm

from web.widgets import SemanticChoiceInput, SemanticDateTimeInput
from .models import Announcement


class AnnouncementForm(ModelForm):
    class Meta:
        model = Announcement
        fields = '__all__'
        widgets = {
            'classification': SemanticChoiceInput(),
            'display_from': SemanticDateTimeInput(attrs={'end_calendar': 'display_to'}),
            'display_to': SemanticDateTimeInput(attrs={'start_calendar': 'display_from', 'default_blank': True}),
        }
