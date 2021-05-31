from django import forms


class ProfileImageInput(forms.FileInput):
    template_name = "checkin/forms/widgets/profile_image.html"

    def is_hidden(self):
        return True
