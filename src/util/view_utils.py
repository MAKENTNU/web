import copy
from abc import ABC
from collections.abc import Iterable
from http import HTTPStatus
from typing import Any

from django.forms import BoundField, FileInput, Form
from django.http import Http404, JsonResponse, QueryDict
from django.utils.translation import gettext_lazy as _
from django.views.generic.base import TemplateResponseMixin
from django.views.generic.edit import FormMixin


def insert_form_field_values(form_kwargs: dict, field_name_to_value: dict[str, Any]):
    # If the request contains posted data:
    if 'data' in form_kwargs:
        data: QueryDict = form_kwargs['data'].copy()
        for field_name, value in field_name_to_value.items():
            data[field_name] = value
        data._mutable = False
        form_kwargs['data'] = data
    return form_kwargs


# noinspection PyUnresolvedReferences
class QueryParameterFormMixin(FormMixin, ABC):
    query_params: dict = None
    """
    This will be a ``dict`` in inheriting views' ``get()`` as long as ``get_form()`` returns a form.
    (If the form contains errors, ``get()`` won't be called.)
    """

    ignore_params_not_on_form = False
    """If ``False``, responds with an error code if any of the request's query parameter fields is not defined on the form class."""

    _query_param_errors: dict = None

    def get(self, request, *args, **kwargs):
        # This check allows inheriting views to potentially call `validate_query_params()` before this method is called,
        # without having to repeat the same validation
        if self._query_param_errors is None:
            self.validate_query_params()

        if self._query_param_errors is None:
            # The form validation logic was skipped, so have to return the default implementation
            return super().get(request, *args, **kwargs)

        if self._query_param_errors:
            return self.form_invalid(form=None)
        else:
            return self.form_valid(form=None, *args, **kwargs)

    def validate_query_params(self):
        form: Form = self.get_form()
        if not form:
            return

        errors = {}
        if not form.is_valid():
            errors['field_errors'] = form.errors

        self.update_errors_with_params_not_on_form(errors, form)

        self._query_param_errors = errors
        if not errors:
            self.query_params = form.cleaned_data

    def update_errors_with_params_not_on_form(self, errors: dict, form: Form):
        if not self.ignore_params_not_on_form:
            fields_not_on_form = self.request.GET.keys() - form.base_fields.keys()
            if fields_not_on_form:
                errors['undefined_fields'] = {
                    'message': "These provided fields are not defined in the API.",
                    'fields': list(fields_not_on_form),
                }

    def get_form(self, form_class=None):
        # This makes the form validation logic optional, by skipping it in the methods above
        if not form_class and not self.get_form_class():
            return None
        return super().get_form(form_class=form_class)

    def get_form_kwargs(self):
        return {
            **super().get_form_kwargs(),
            'data': self.request.GET,
        }

    def form_valid(self, form=None, *get_args, **get_kwargs):
        return super().get(self.request, *get_args, **get_kwargs)

    def form_invalid(self, form=None, *, errors: dict = None, status=HTTPStatus.BAD_REQUEST):
        return UTF8JsonResponse(errors or self._query_param_errors, status=status)


class CustomFieldsetFormMixin(TemplateResponseMixin, FormMixin, ABC):
    template_name = 'web/generic_form.html'

    base_template = 'web/base.html'
    form_title: str
    narrow = True
    centered_title = True
    back_button_link: str
    back_button_text: str
    save_button_text = _("Save")
    cancel_button = True
    right_floated_buttons = True
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
            'cancel_button': self.cancel_button,
            'right_floated_buttons': self.right_floated_buttons,
            'fieldsets': fieldsets,

            'has_file_field': self._has_file_field,
        })
        return context

    def compile_fieldsets(self, custom_fieldsets: Iterable[dict], form: Form):
        fieldsets = []
        for fieldset in copy.deepcopy(custom_fieldsets):
            if not fieldset:
                continue

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
    # A whitelist is being used here, but it should be mentioned that the main strings we want to blacklist, are strings starting with:
    # * word characters (i.e. not symbols), as this allows for arbitrary absolute URLs (e.g. `google.com` or `http://google.com`);
    # * `//`, as this allows for protocol-relative URLs (e.g. `//google.com`).
    allowed_next_params = set()

    cleaned_next_param: str | None

    def dispatch(self, request, *args, **kwargs):
        next_param = request.GET.get('next')
        if next_param and next_param not in self.get_allowed_next_params():
            # Remove the `next` param from the query dict
            get_dict: QueryDict = request.GET.copy()
            get_dict['next'] = None
            get_dict._mutable = False
            request.GET = get_dict

            next_param = None
        self.cleaned_next_param = next_param
        return super().dispatch(request, *args, **kwargs)

    def get_allowed_next_params(self) -> set[str]:
        return self.allowed_next_params


class UTF8JsonResponse(JsonResponse):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **{
            'json_dumps_params': {'ensure_ascii': False},  # Prevents replacing unicode characters with \u encoding
            **kwargs,
        })
