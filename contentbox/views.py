from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import path, reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, UpdateView

from util.view_utils import CustomFieldsetFormMixin
from .forms import ContentBoxForm, EditSourceContentBoxForm
from .models import ContentBox


class DisplayContentBoxView(DetailView):
    model = ContentBox
    template_name = 'contentbox/display.html'
    context_object_name = 'contentbox'
    extra_context = {
        'base_template': 'web/base.html',
    }

    change_perms = ('contentbox.change_contentbox',)

    # The value of this field is set when calling the view's `as_view()` method
    title = ""

    def get_object(self, queryset=None):
        contentbox, _created = ContentBox.objects.get_or_create(title=self.title)
        return contentbox

    def get_context_data(self, **kwargs):
        return {
            'user_can_change': self.request.user.has_perms(self.get_change_perms()),
            **super().get_context_data(**kwargs),
        }

    def get_change_perms(self):
        return self.change_perms + self.get_object().extra_change_perms_str_tuple

    @classmethod
    def get_path(cls, title: str):
        return path(f'{title}/', cls.as_view(title=title), name=title)

    @classmethod
    def get_multi_path(cls, title: str, alt_url1: str, *other_alt_urls: str) -> tuple:
        alt_urls = (alt_url1, *other_alt_urls)
        return (
            path(f'{title}/', cls.as_view(title=title), name=title),
            *(path(f'{url}/', cls.as_view(title=title)) for url in alt_urls),
        )


class EditContentBoxView(PermissionRequiredMixin, CustomFieldsetFormMixin, UpdateView):
    permission_required = ('contentbox.change_contentbox',)
    model = ContentBox
    form_class = ContentBoxForm
    template_name = 'contentbox/edit.html'

    narrow = False

    def get_permission_required(self):
        return self.permission_required + self.get_object().extra_change_perms_str_tuple

    def get_form_class(self):
        # Allow editing HTML source code if this permission is required by the view
        # (not if the user has the permission or not, as that is handled by `PermissionRequiredMixin`):
        if 'internal.can_change_rich_text_source' in self.get_permission_required():
            return EditSourceContentBoxForm
        return super().get_form_class()

    def get_form_title(self):
        return _("Edit “{title}”").format(title=self.object.title)

    def get_back_button_link(self):
        return self.get_success_url()

    def get_back_button_text(self):
        return _("View “{title}”").format(title=self.object.title)

    def get_success_url(self):
        return reverse(self.object.title)
