from django import forms

from ..models.reservation import Reservation


class APIMachineDataQueryForm(forms.Form):
    exclude_reservation = forms.ModelChoiceField(
        Reservation.objects.all(),
        required=False,
        error_messages={
            'invalid_choice': "Reservation with pk=%(value)s was not found."
        },
    )


class APIReservationListQueryForm(forms.Form):
    start_date = forms.DateTimeField()
    end_date = forms.DateTimeField()

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date:
            if start_date > end_date:
                code = 'invalid_relative_to_other_field'
                raise forms.ValidationError({
                    'start_date': forms.ValidationError("This must be before 'end_date'.", code=code),
                    'end_date': forms.ValidationError("This must be after 'start_date'.", code=code),
                })

        return cleaned_data
