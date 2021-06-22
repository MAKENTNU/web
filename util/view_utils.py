import copy
import re
from abc import ABC
from typing import Any, Iterable, Optional, Tuple

from django.forms import BoundField, FileInput, Form
from django.http import Http404, QueryDict
from django.utils.translation import gettext_lazy as _
from django.views.generic.base import TemplateResponseMixin
from django.views.generic.edit import FormMixin


def insert_form_field_values(form_kwargs: dict, *field_names_to_values: Tuple[str, Any]):
    # If the request contains posted data:
    if 'data' in form_kwargs:
        data = form_kwargs['data'].copy()
        for field_name, value in field_names_to_values:
            data[field_name] = value
        form_kwargs['data'] = data
    return form_kwargs


class CustomFieldsetFormMixin(TemplateResponseMixin, FormMixin, ABC):
    template_name = 'web/edit_form.html'

    base_template = 'web/base.html'
    form_title: str
    narrow = True
    centered_title = True
    back_button_link: str
    back_button_text: str
    save_button_text = _("Save")
    custom_fieldsets: Iterable[dict] = None

    _has_file_field = False

    def get_form_title(self):
        return self.form_title

    def get_back_button_link(self):
        return self.back_button_link

    def get_back_button_text(self):
        return self.back_button_text

    def get_custom_fieldsets(self):
        return self.custom_fieldsets

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = context['form']

        custom_fieldsets = self.get_custom_fieldsets()
        if not custom_fieldsets:
            custom_fieldsets = [
                {'fields': tuple(rendered_field.name for rendered_field in form)},
            ]
        fieldsets = self.compile_fieldsets(custom_fieldsets, form)

        context.update({
            'base_template': self.base_template,
            'form_title': self.get_form_title(),
            'narrow': self.narrow,
            'centered_title': self.centered_title,
            'back_button_link': self.get_back_button_link(),
            'back_button_text': self.get_back_button_text(),
            'save_button_text': self.save_button_text,
            'fieldsets': fieldsets,

            'has_file_field': self._has_file_field,
        })
        return context

    def compile_fieldsets(self, custom_fieldsets: Iterable[dict], form: Form):
        fieldsets = []
        for fieldset in copy.deepcopy(custom_fieldsets):
            if 'heading' in fieldset:
                fieldset['type'] = 'heading'
            else:
                fieldset['type'] = 'fieldset'
                rendered_fields = []
                for field_name in fieldset['fields']:
                    if not field_name:
                        continue
                    try:
                        rendered_field = form[field_name]
                    except KeyError as e:
                        raise KeyError(f"'{field_name}' was not found among the fields of {type(form)}") from e
                    # Don't render hidden fields; the view should manually fill them with a value when submitted
                    if rendered_field.is_hidden:
                        continue

                    self.run_field_checks(rendered_field)
                    rendered_fields.append(rendered_field)
                fieldset['fields'] = tuple(rendered_fields)

            fieldsets.append(fieldset)
        return fieldsets

    def run_field_checks(self, rendered_field: BoundField):
        if rendered_field.widget_type == 'checkbox':
            # Set custom attribute for use in the template
            rendered_field.is_checkbox = True
        if isinstance(rendered_field.field.widget, FileInput):
            self._has_file_field = True


class PreventGetRequestsMixin:

    def get(self, *args, **kwargs):
        raise Http404()


# noinspection PyUnresolvedReferences
class CleanNextParamMixin:
    # It should either be just a `/` (meaning the front page),
    # or a `/` followed by one or more word characters and the rest of the string (due to no `$` anchor).
    # A whitelist was chosen here, but it should be mentioned that the main strings we want to blacklist, are strings starting with:
    # * word characters (i.e. not symbols), as this allows for arbitrary absolute URLs (e.g. `google.com` or `http://google.com`);
    # * `//`, as this allows for protocol-relative URLs (e.g. `//google.com`).
    SAFE_NEXT_REGEX = re.compile(r"^(/$|/\w+)")

    cleaned_next_param: Optional[str]

    def dispatch(self, request, *args, **kwargs):
        next_param = request.GET.get('next')
        if next_param and not self.SAFE_NEXT_REGEX.match(next_param):
            # Remove the `next` param from the query dict
            get_dict: QueryDict = request.GET.copy()
            get_dict['next'] = None
            get_dict._mutable = False
            request.GET = get_dict

            next_param = None
        self.cleaned_next_param = next_param
        return super().dispatch(request, *args, **kwargs)
