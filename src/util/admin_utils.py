import copy
from collections.abc import Callable

from django.contrib import admin
from django.contrib.admin.widgets import (
    AdminTextInputWidget,
    AdminURLFieldWidget,
    ForeignKeyRawIdWidget,
)
from django.db import models
from django.db.models import Model, QuerySet
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from sorl.thumbnail.admin.current import AdminImageWidget

from card.modelfields import CardNumberField
from card.widgets import CardNumberInput
from users.models import User
from util.html_utils import escape_to_named_characters
from util.templatetags.html_tags import anchor_tag
from web.modelfields import URLTextField, UnlimitedCharField
from web.multilingual.admin import create_multi_lingual_admin_formfield


def link_to_admin_change_form(obj: Model, *, text=None, should_open_new_tab=True):
    """
    Constructs a string consisting of an ``<a>`` tag which links to the Django admin change form of ``obj``.
    The tag's text is set to ``text``, or ``obj`` if not given.
    If ``should_open_new_tab`` is ``True``, the link is opened in a new tab or window when clicked.
    """
    url = reverse(
        f"admin:{obj._meta.app_label}_{obj._meta.model_name}_change", args=[obj.pk]
    )
    return anchor_tag(url, text or obj, target_blank=should_open_new_tab)


def search_escaped_and_unescaped(
    super_obj: admin.ModelAdmin, request, input_queryset: QuerySet, search_term: str
):
    """
    Can be called from the ``get_search_results()`` method of ``ModelAdmin`` classes, to search using both escaped and unescaped characters.
    For example, passing in "grøt" as ``search_term``, will search for both "grøt" and "gr&oslash;t".
    """
    # `use_distinct` starts as `False` in Django's `get_search_results()`
    combined_searched_querysets, use_distinct_result = input_queryset.none(), False
    # Try both with and without escaping:
    for search_term_repr in (search_term, escape_to_named_characters(search_term)):
        searched_queryset, use_distinct = super_obj.get_search_results(
            request, input_queryset, search_term_repr
        )
        combined_searched_querysets = combined_searched_querysets.union(
            # Clear ordering
            searched_queryset.order_by()
        )
        use_distinct_result |= use_distinct

    result_queryset = input_queryset.filter(
        pk__in={cb.pk for cb in combined_searched_querysets}
    )
    return result_queryset, use_distinct_result


# noinspection PyUnresolvedReferences
class UserSearchFieldsMixin:
    user_lookup: str  # E.g. 'user__'
    name_for_full_name_lookup: str  # E.g. 'full_name'; used in `User.get_user_search_fields()` and `User.annotate_full_name()`

    def get_search_fields(self, request):
        search_fields = super().get_search_fields(request)
        return search_fields + User.get_user_search_fields(
            self.user_lookup, annotated_full_name_lookup=self.name_for_full_name_lookup
        )

    def get_search_results(self, request, queryset, search_term):
        queryset = User.annotate_full_name(
            queryset, self.user_lookup, lookup_name=self.name_for_full_name_lookup
        )
        return super().get_search_results(request, queryset, search_term)


# noinspection PyUnresolvedReferences
class DefaultAdminWidgetsMixin:
    """Overrides the Django admin change forms' widgets with the default ones used in this project."""

    formfield_overrides = {
        models.ImageField: {"widget": AdminImageWidget},
        CardNumberField: {"widget": CardNumberInput},
        UnlimitedCharField: {"widget": AdminTextInputWidget},
        URLTextField: {"widget": AdminURLFieldWidget},
    }
    enable_changing_rich_text_source = False

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        multi_lingual_admin_formfield = create_multi_lingual_admin_formfield(
            db_field,
            request,
            **kwargs,
            enable_changing_rich_text_source=self.enable_changing_rich_text_source,
        )
        if multi_lingual_admin_formfield:
            return multi_lingual_admin_formfield

        if db_field.choices:
            return self.formfield_for_choice_field(db_field, request, **kwargs)

        # Code based on https://github.com/django/django/blob/fbea64b8ce6a82dd34b1f78cb884306455106185/django/contrib/admin/options.py#L181-L184
        for klass in db_field.__class__.mro():
            if klass in self.formfield_overrides:
                formfield_overrides_kwargs = copy.deepcopy(
                    self.formfield_overrides[klass]
                )
                new_kwargs = formfield_overrides_kwargs | kwargs
                # Always override the widget:
                widget = formfield_overrides_kwargs.get("widget")
                if widget:
                    new_kwargs["widget"] = widget
                return db_field.formfield(**new_kwargs)

        return super().formfield_for_dbfield(db_field, request, **kwargs)


# Code based on https://github.com/Uninett/Argus/commit/bc6031e2f9de3e14a942f3f20bfa1e6c7d37d637
class YesNoListFilter(admin.SimpleListFilter):
    YES = 1
    NO = 0

    title: str
    # Parameter for the filter that will be used in the URL query
    parameter_name: str

    get_filter_func: Callable[[], Callable[[QuerySet, bool], QuerySet]]

    def lookups(self, request, model_admin):
        return (
            (self.YES, _("Yes")),
            (self.NO, _("No")),
        )

    def queryset(self, request, queryset):
        try:
            value = int(self.value())
        except (TypeError, ValueError):
            return None

        if value not in {self.YES, self.NO}:
            return None

        return self.get_filter_func()(queryset, bool(value))


# Code based on https://github.com/Uninett/Argus/commit/bc6031e2f9de3e14a942f3f20bfa1e6c7d37d637
def list_filter_factory(
    title: str, parameter_name: str, filter_func: Callable[[QuerySet, bool], QuerySet]
):
    new_class_name = f"{parameter_name.title().replace('_', '')}ListFilter"
    new_class_members = {
        "title": title,
        "parameter_name": parameter_name,
        # Can't pass `filter_func` directly, as calling it from the new class (`self.filter_func()`)
        # will pass an extra `self` argument
        "get_filter_func": lambda _self: filter_func,
    }
    new_class = type(new_class_name, (YesNoListFilter,), new_class_members)
    return new_class


# noinspection PyUnresolvedReferences
class LabelFreeRawIdWidgetAdminMixin:
    """
    Extending this class can help reducing the number of database queriees done by Django's ``ForeignKeyRawIdWidget``,
    if the ``__str__()`` method of the admin class' model uses values from related fields.
    """

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name not in self.raw_id_fields:
            return super().formfield_for_foreignkey(db_field, request, **kwargs)

        class LabelFreeRawIdWidget(ForeignKeyRawIdWidget):
            def label_and_url_for_value(self, value):
                return "", ""

        kwargs["widget"] = LabelFreeRawIdWidget(
            db_field.remote_field, self.admin_site, using=kwargs.get("using")
        )
        return db_field.formfield(**kwargs)
