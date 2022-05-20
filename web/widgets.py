import json
from enum import Enum
from typing import Any, Callable, Dict

import ckeditor.widgets
import ckeditor_uploader.widgets
import django.forms as forms
from django.conf import settings
from django.forms.widgets import ChoiceWidget
from django.utils.translation import gettext_lazy as _
from js_asset import JS


class SemanticTimeInput(forms.TimeInput):
    template_name = 'web/forms/widgets/semantic_time.html'


class SemanticDateInput(forms.DateInput):
    template_name = 'web/forms/widgets/semantic_date.html'

    class Media:
        js = ('web/js/date_utils.js',)


class SemanticDateTimeInput(forms.DateTimeInput):
    template_name = 'web/forms/widgets/semantic_datetime.html'

    class Media:
        js = ('web/js/date_utils.js',)


class SelectWithDataAttrsMixin(ChoiceWidget):
    """
    An extension of the ``ChoiceWidget`` (which ``Select`` and ``SelectMultiple`` extends)
    which allows adding data attributes to each option of the widget's generated ``<select>`` tag.
    """

    def __init__(self, attr_name_to_attr_value_getter: Dict[str, Callable[[Any], Any]] = None, *args, **kwargs):
        """
        :param attr_name_to_attr_value_getter: A dictionary that maps from the name of the data attribute to add,
                                               to a function that accepts the option's value and returns the value of the data attribute.
                                               If the function returns ``None``, the data attribute will not be added.
        """
        super().__init__(*args, **kwargs)

        if attr_name_to_attr_value_getter:
            self.attr_name_to_attr_value_getter = attr_name_to_attr_value_getter
            self._create_option_override_func = self._create_option_with_data_attrs
        else:
            self._create_option_override_func = self._create_option_passthrough

    def create_option(self, name, value, *args, **kwargs):
        return self._create_option_override_func(name, value, *args, **kwargs)

    def _create_option_passthrough(self, *args, **kwargs):
        return super().create_option(*args, **kwargs)

    def _create_option_with_data_attrs(self, name, value, *args, **kwargs):
        option_dict = super().create_option(name, value, *args, **kwargs)

        for attr_name, attr_value_getter in self.attr_name_to_attr_value_getter.items():
            attr_value = attr_value_getter(value)
            if attr_value is not None:
                option_dict['attrs'][f'data-{attr_name}'] = attr_value

        return option_dict


class SemanticChoiceInput(SelectWithDataAttrsMixin, forms.Select):
    template_name = 'web/forms/widgets/semantic_select.html'


class SemanticSearchableChoiceInput(SelectWithDataAttrsMixin, forms.Select):
    template_name = 'web/forms/widgets/semantic_search_select.html'
    prompt_text = _("Choose value")

    def __init__(self, *args, **kwargs):
        super().__init__(attrs=kwargs.pop("attrs", {}))
        self.attrs['prompt_text'] = kwargs.pop('prompt_text', self.prompt_text)
        self.attrs['force_selection'] = kwargs.pop('force_selection', False)


class SemanticMultipleSelectInput(SelectWithDataAttrsMixin, forms.SelectMultiple):
    template_name = 'web/forms/widgets/semantic_select_multiple.html'
    prompt_text = _("Choose value")

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.attrs['prompt_text'] = kwargs.pop('prompt_text', self.prompt_text)


class SemanticFileInput(forms.ClearableFileInput):
    template_name = 'web/forms/widgets/semantic_file.html'

    class Media:
        css = {
            'all': ('web/css/forms/widgets/semantic_file.css',),
        }

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context.update({
            "FILE_MAX_SIZE": settings.FILE_MAX_SIZE,
        })
        return context


class Direction(Enum):
    HORIZONTAL = 'H'
    VERTICAL = 'V'


class DirectionalCheckboxSelectMultiple(forms.CheckboxSelectMultiple):
    # The values go from 2 to 16, to match Fomantic-UI's CSS classes
    NUMBERS_TO_WORDS = {
        2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine",
        10: "ten", 11: "eleven", 12: "twelve", 13: "thirteen", 14: "fourteen", 15: "fifteen", 16: "sixteen",
    }

    template_name = 'web/forms/widgets/directional_checkbox_select.html'
    option_template_name = 'web/forms/widgets/directional_checkbox_option.html'

    def __init__(self, direction: Direction, container_classes=None, option_classes=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.direction = direction
        self.container_classes = container_classes
        self.option_classes = option_classes

    def get_container_classes(self):
        if self.container_classes:
            return self.container_classes
        else:
            if self.direction == Direction.HORIZONTAL:
                return f"{self.NUMBERS_TO_WORDS.get(len(self.choices), '')} fields"
            elif self.direction == Direction.VERTICAL:
                return "list"
        return ""

    def get_option_classes(self):
        if self.option_classes:
            return self.option_classes
        else:
            if self.direction == Direction.HORIZONTAL:
                return "field"
            elif self.direction == Direction.VERTICAL:
                return "item"
        return ""

    def get_context(self, *args, **kwargs):
        context = super().get_context(*args, **kwargs)
        context['widget']['container_classes'] = self.get_container_classes()
        return context

    def create_option(self, *args, **kwargs):
        options = super().create_option(*args, **kwargs)
        options['option_classes'] = self.get_option_classes()
        options['is_vertical'] = self.direction == Direction.VERTICAL
        return options


class MazeMapSearchInput(forms.TextInput):
    """
    Widget that enables MazeMap search functionality, including autofill of URL to MazeMap.
    """
    template_name = 'web/forms/widgets/mazemap_search.html'
    required_class_attr = 'prompt'
    placeholder = _("Search places")

    class Media:
        js = ('web/js/forms/widgets/mazemap_search.js',)

    def __init__(self, campus_id=1, max_results=5, url_field=None, attrs=None):
        """
        :param campus_id: Campus to search for points of interest on. Default: NTNU Gløshaugen
        :param max_results: Maximum number of search results to return
        :param url_field: Field to autofill with MazeMap URL. If None, autofill functionality is turned off
        :param attrs: HTML attributes for the <input> element
        """

        default_attrs = {
            'placeholder': self.placeholder,
            'data-campus-id': campus_id,
            'data-max-results': max_results,
            'data-url-field': url_field,
        }
        if attrs:
            default_attrs.update(attrs)

        default_attrs['class'] = f"{default_attrs.get('class', '')} {self.required_class_attr}"

        super().__init__(attrs=default_attrs)


class CKEditorWidget(ckeditor.widgets.CKEditorWidget):
    """
    A subclass of CKEditor's base widget, which adds a linked JavaScript file that enables the user to change the HTML source code directly
    (including adding ``script`` tags) through an added "Source" toolbar button.

    NOTE: Make sure that the user has the ``internal.can_change_rich_text_source`` permission before using this widget.
    """

    def __init__(self, *args, **kwargs):
        self.config_name = kwargs.get('config_name', None)
        super().__init__(*args, **kwargs)

    # See https://docs.djangoproject.com/en/stable/topics/forms/media/#media-as-a-dynamic-property
    @property
    def media(self):
        config_data_attrs = {
            # Boolean values should be converted to strings (for use by JavaScript), as the `JS` class does not properly support boolean attributes
            'should-allow-all-tags': json.dumps(self.config_name == settings.CKEDITOR_EDIT_SOURCE_CONFIG_NAME),
        }
        return forms.Media(
            js=(
                JS('ckeditor/ckeditor/config_from_django.js', attrs={
                    'id': 'config-from-django',
                    **{f"data-{name}": value for name, value in config_data_attrs.items()},
                }),
            ),
        ) + super().media


class CKEditorUploadingWidget(CKEditorWidget, ckeditor_uploader.widgets.CKEditorUploadingWidget):
    pass
