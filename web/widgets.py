from enum import Enum

import django.forms as forms
from django.conf import settings
from django.utils.translation import gettext_lazy as _


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


class SemanticChoiceInput(forms.Select):
    template_name = 'web/forms/widgets/semantic_select.html'


class SemanticSearchableChoiceInput(forms.Select):
    template_name = 'web/forms/widgets/semantic_search_select.html'
    prompt_text = _("Choose value")

    def __init__(self, *args, **kwargs):
        super().__init__(attrs=kwargs.pop("attrs", {}))
        self.attrs['prompt_text'] = kwargs.pop('prompt_text', self.prompt_text)
        self.attrs['force_selection'] = kwargs.pop('force_selection', False)


class SemanticMultipleSelectInput(forms.SelectMultiple):
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


class MazemapSearchInput(forms.TextInput):
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
            'data-campusId': campus_id,
            'data-maxResults': max_results,
            'data-urlField': url_field,
        }
        if attrs:
            default_attrs.update(attrs)

        default_attrs['class'] = f"{default_attrs.get('class', '')} {self.required_class_attr}"

        super().__init__(attrs=default_attrs)
