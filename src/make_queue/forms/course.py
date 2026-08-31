from django import forms
from django.db.models import Q
from django.utils.text import capfirst
from django.utils.translation import gettext_lazy as _

from card import utils as card_utils
from card.formfields import CardNumberField
from make_queue.course_import import CourseImportError, ImportedRow, parse_rows
from make_queue.models.course import CoursePermission, Printer3DCourse
from users.models import User
from util.spreadsheet_utils import SUPPORTED_SUFFIXES, SpreadsheetReadError, read_rows
from web.widgets import (
    SemanticChoiceInput,
    SemanticDateInput,
    SemanticSearchableChoiceInput,
)


class Printer3DCourseForm(forms.ModelForm):
    card_number = CardNumberField(required=False)

    class Meta:
        model = Printer3DCourse
        exclude = ["_card_number"]
        widgets = {
            "status": SemanticChoiceInput(),
            "date": SemanticDateInput(),
            "username": forms.TextInput(attrs={"autofocus": "autofocus"}),
            "course_permissions": forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)
        if self.instance.user:
            queryset = User.objects.filter(Q(printer_3d_course=self.instance))
        else:
            queryset = User.objects.filter(Q(printer_3d_course=None))
        self.fields["user"] = forms.ModelChoiceField(
            queryset=queryset,
            required=False,
            widget=SemanticSearchableChoiceInput(prompt_text=_("Select user")),
            label=Printer3DCourse._meta.get_field("user").verbose_name,
        )
        if self.instance.card_number is not None:
            self.initial["card_number"] = self.instance.card_number

        self.fields["course_permissions"].queryset = (
            self.fields["course_permissions"]
            .queryset.exclude(short_name="AUTH")
            .exclude(short_name=CoursePermission.DefaultPerms.TAKEN_3D_PRINTER_COURSE)
            .order_by("name")
        )
        self.fields["course_permissions"].widget.attrs["class"] = "ui fluid checkbox"

        self.base_permission = CoursePermission.objects.get(
            short_name=CoursePermission.DefaultPerms.TAKEN_3D_PRINTER_COURSE
        )
        if not self.instance.pk:
            self.initial["course_permissions"] = self.fields[
                "course_permissions"
            ].queryset.filter(short_name="VRON")

    def clean_card_number(self):
        card_number: str = self.cleaned_data["card_number"]
        if card_number:
            # This accident prevention was requested by the Mentor committee.
            # Phone number is from https://i.ntnu.no/wiki/-/wiki/Norsk/Vakt+og+service+p%C3%A5+campus
            if card_number.lstrip("0") == "91897373":
                message = _(
                    # Translators: See the Norwegian and English versions of this page
                    # for a translation of "Building security": https://i.ntnu.no/wiki/-/wiki/Norsk/Vakt+og+service+p%C3%A5+campus
                    "The card number was detected to be the phone number of"
                    " Building security at NTNU. Please enter a valid card number."
                )
                raise forms.ValidationError(message)
        return card_number

    def clean_course_permissions(self):
        course_permissions = set(self.cleaned_data["course_permissions"])
        course_permissions.add(self.base_permission)
        return list(course_permissions)

    def clean(self):
        cleaned_data = super().clean()
        card_number = cleaned_data.get("card_number")
        username = cleaned_data.get("username")

        if card_number and username:
            if card_utils.is_duplicate(card_number, username):
                message = _("Card number is already in use")
                raise forms.ValidationError({"card_number": message})
        return cleaned_data

    def save(self, commit=True):
        course = super().save(commit=False)
        course.card_number = self.cleaned_data["card_number"]
        course.save()
        course.course_permissions.set(self.cleaned_data["course_permissions"])

        return course


class Printer3DCourseImportForm(forms.Form):
    """Uploading of a spreadsheet with several course registrations at once."""

    # Uploading a bigger file than this would in any case time out the request
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MiB

    file = forms.FileField(
        label=_("File"),
        help_text=_(
            "A CSV or XLSX file with one course participant per row, and the columns"
            " named by a header row."
        ),
        widget=forms.ClearableFileInput(attrs={"accept": ",".join(SUPPORTED_SUFFIXES)}),
    )
    date = forms.DateField(
        label=capfirst(_("default course date")),
        help_text=_("Used for the rows that have no course date of their own."),
        widget=SemanticDateInput(),
    )
    status = forms.ChoiceField(
        choices=Printer3DCourse.Status.choices,
        initial=Printer3DCourse.Status.REGISTERED,
        label=capfirst(Printer3DCourse._meta.get_field("status").verbose_name),
        widget=SemanticChoiceInput(),
    )
    course_permissions = forms.ModelMultipleChoiceField(
        queryset=CoursePermission.objects.none(),
        required=False,
        label=capfirst(
            Printer3DCourse._meta.get_field("course_permissions").verbose_name
        ),
        widget=forms.CheckboxSelectMultiple(attrs={"class": "ui fluid checkbox"}),
    )
    skip_already_registered = forms.BooleanField(
        required=False,
        initial=True,
        label=_("Skip participants that are already registered"),
        help_text=_(
            "When unchecked, an already registered username is counted as an error"
            " instead of being silently skipped."
        ),
    )
    import_valid_rows_only = forms.BooleanField(
        required=False,
        label=_("Import the valid rows even if some rows have errors"),
        help_text=_(
            "When unchecked, nothing is imported unless every row is valid, which"
            " makes it safe to upload the same file again after fixing the errors."
        ),
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.fields["course_permissions"].queryset = (
            CoursePermission.objects.exclude(short_name="AUTH")
            .exclude(short_name=CoursePermission.DefaultPerms.TAKEN_3D_PRINTER_COURSE)
            .order_by("name")
        )
        self.initial.setdefault(
            "course_permissions",
            self.fields["course_permissions"].queryset.filter(short_name="VRON"),
        )
        # The rows of the uploaded file, set by `clean_file()`
        self.imported_rows: list[ImportedRow] = []

    def clean_file(self):
        uploaded_file = self.cleaned_data["file"]
        if uploaded_file.size > self.MAX_FILE_SIZE:
            message = _("The file is too big; the maximum size is %(max_size)d MB.")
            raise forms.ValidationError(
                message % {"max_size": self.MAX_FILE_SIZE // (1024 * 1024)}
            )

        try:
            rows = read_rows(uploaded_file)
            self.imported_rows = parse_rows(rows)
        except (SpreadsheetReadError, CourseImportError) as e:
            raise forms.ValidationError(str(e)) from e
        return uploaded_file
