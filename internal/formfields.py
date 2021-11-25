from django import forms
from django.conf import settings
from phonenumber_field.formfields import PhoneNumberField
from phonenumber_field.phonenumber import PhoneNumber, to_python
from phonenumbers.phonenumberutil import region_code_for_number


# Code based on:
# https://github.com/stefanfoulis/django-phonenumber-field/blob/9412f0fb5f713f918c3e4825ff11084ff0d5a2b9/phonenumber_field/formfields.py#L34-L55
# This should be removed if/when https://github.com/stefanfoulis/django-phonenumber-field/pull/250 has been merged
class PhoneNumberRegionFallbackField(PhoneNumberField):
    def __init__(self, *args, **kwargs):
        self.default_region = kwargs.pop('region', settings.PHONENUMBER_DEFAULT_REGION)
        super().__init__(*args, **kwargs)

    def prepare_value(self, value):
        """Show numbers in the 'default_region' without region code."""
        if isinstance(value, PhoneNumber):
            if self.default_region == region_code_for_number(value):
                return value.as_national
            else:
                return value.as_international
        return value

    def to_python(self, value):
        """Consider numbers without region code numbers in 'default_region'."""
        if value in self.empty_values:
            return self.empty_value
        phone_number = to_python(value, self.default_region)
        if phone_number and not phone_number.is_valid():
            raise forms.ValidationError(self.error_messages['invalid'])
        return phone_number
