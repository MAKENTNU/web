from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import Http404
from django.urls import NoReverseMatch, path, reverse
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _, pgettext
from django.views.generic import DetailView, UpdateView

from util.view_utils import CustomFieldsetFormMixin
from .forms import ContentBoxForm, EditSourceContentBoxForm
from .models import ContentBox


class ContentBoxDetailView(DetailView):
    model = ContentBox
    template_name = 'contentbox/content_box_detail.html'
    context_object_name = 'contentbox'
    extra_context = {
        'base_template': 'web/base.html',
    }

    change_perms = ('contentbox.change_contentbox',)

    # The value of this field is set when calling the view's `as_view()` method
    url_name = None

    def get_object(self, queryset=None):
        contentbox, _created = ContentBox.objects.get_or_create(url_name=self.url_name)
        return contentbox

    def get_context_data(self, **kwargs):
        return {
            'user_can_change': self.request.user.has_perms(self.get_change_perms()),
            **super().get_context_data(**kwargs),
        }

    def get_change_perms(self):
        return self.change_perms + self.get_object().extra_change_perms_str_tuple

    @classmethod
    def get_path(cls, url_name: str):
        return path(f'{url_name}/', cls.as_view(url_name=url_name), name=url_name)

    @classmethod
    def get_multi_path(cls, url_name: str, alt_url1: str, *other_alt_urls: str) -> tuple:
        alt_urls = (alt_url1, *other_alt_urls)
        return (
            path(f'{url_name}/', cls.as_view(url_name=url_name), name=url_name),
            *(path(f'{url}/', cls.as_view(url_name=url_name)) for url in alt_urls),
        )


class ContentBoxUpdateView(PermissionRequiredMixin, CustomFieldsetFormMixin, UpdateView):
    permission_required = ('contentbox.change_contentbox',)
    model = ContentBox
    form_class = ContentBoxForm
    template_name = 'contentbox/content_box_form.html'

    narrow = False

    def get_object(self, *args, **kwargs):
        obj: ContentBox = super().get_object(*args, **kwargs)
        try:
            reverse(obj.url_name)
        except NoReverseMatch:
            raise Http404(f"Unable to find the URL for the ContentBox with url_name '{obj.url_name}'")
        return obj

    def get_permission_required(self):
        return self.permission_required + self.get_object().extra_change_perms_str_tuple

    def get_form_class(self):
        # Allow editing HTML source code if this permission is required by the view
        # (not if the user has the permission or not, as that is handled by `PermissionRequiredMixin`):
        if 'internal.can_change_rich_text_source' in self.get_permission_required():
            return EditSourceContentBoxForm
        return super().get_form_class()

    def get_form_title(self):
        return self._get_page_title(_("Edit"))

    def _get_page_title(self, prefixed_verb: str = None):
        prefix = f"{prefixed_verb} " if prefixed_verb else ""
        html_text = f"{prefix}<code>{self.object.url_name}</code> (<code>{self.get_success_url()}</code>)"
        return mark_safe(html_text)

    def get_back_button_link(self):
        return self.get_success_url()

    def get_back_button_text(self):
        return self._get_page_title(pgettext("view page", "View"))

    def get_success_url(self):
        return reverse(self.object.url_name)
