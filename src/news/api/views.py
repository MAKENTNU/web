from abc import ABC

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.views.generic import FormView
from django.views.generic.detail import SingleObjectMixin

from util.view_utils import PreventGetRequestsMixin, UTF8JsonResponse
from ..forms import ToggleForm
from ..models import Article, Event, TimePlace
from ..views.event import TimePlaceRelatedViewMixin


class AdminAPINewsBaseToggleView(PreventGetRequestsMixin, SingleObjectMixin, FormView, ABC):
    form_class = ToggleForm

    def get_form_kwargs(self):
        return {
            **super().get_form_kwargs(),
            'instance': self.get_object(),
        }

    def form_valid(self, form):
        obj = self.get_object()
        toggle_attr = form.cleaned_data['toggle_attr']
        attr_value = getattr(obj, toggle_attr)

        toggled_attr_value = not attr_value
        setattr(obj, toggle_attr, toggled_attr_value)
        obj.save()
        return UTF8JsonResponse({
            'is_hidden': toggled_attr_value,
        })

    def form_invalid(self, form):
        return UTF8JsonResponse({})


class AdminAPIArticleToggleView(PermissionRequiredMixin, AdminAPINewsBaseToggleView):
    permission_required = ('news.change_article',)
    model = Article


class AdminAPIEventToggleView(PermissionRequiredMixin, AdminAPINewsBaseToggleView):
    permission_required = ('news.change_event',)
    model = Event


class AdminAPITimePlaceToggleView(PermissionRequiredMixin, TimePlaceRelatedViewMixin, AdminAPINewsBaseToggleView):
    permission_required = ('news.change_timeplace',)
    model = TimePlace

    def get_object(self, queryset=None):
        return self.time_place
