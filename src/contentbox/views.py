from functools import lru_cache
from urllib.parse import urlparse

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import NoReverseMatch, path, reverse as django_reverse
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _, pgettext
from django.views.generic import DetailView, UpdateView
from django_hosts import reverse

from util.url_utils import get_reverse_host_kwargs_from_url, reverse_admin
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

    # Caches `get_absolute_url()`, as it will be called multiple times
    # (`maxsize` need only be 1, since the cached value is not supposed to last longer than each request)
    @lru_cache(maxsize=1)
    def _absolute_url(self, content_box: ContentBox):
        try:
            return content_box.get_absolute_url()
        except NoReverseMatch:
            return None

    def dispatch(self, request, *args, **kwargs):
        if not self.has_permission():
            return super().dispatch(request, *args, **kwargs)

        content_box: ContentBox = super().get_object()
        # Check if the requested host/subdomain has a registered URL for this content box
        try:
            django_reverse(content_box.url_name)
        except NoReverseMatch:
            # ...if not, check if another subdomain has a registered URL for it
            url_on_other_subdomain = self._absolute_url(content_box)
            if url_on_other_subdomain:
                host_kwargs = get_reverse_host_kwargs_from_url(url_on_other_subdomain)
                change_url = reverse('content_box_update', args=[content_box.pk], **host_kwargs)
                return HttpResponseRedirect(change_url)
            else:
                # We don't know which permissions should be needed to view this page
                # (since e.g. the content boxes on the internal subdomain has different change permissions than those on the main subdomain),
                # so redirect to the Django admin site to be safe
                return render(request, 'contentbox/content_box_form__error_display_url_not_found.html', {
                    'form_title': _("Cannot change this ContentBox on this subdomain"),
                    'django_admin_change_url': reverse_admin('contentbox_contentbox_change', args=[content_box.pk]),
                    'index_page_url': self.request.build_absolute_uri("/"),
                    'base_template': self.base_template,
                })

        return super().dispatch(request, *args, **kwargs)

    def get_permission_required(self):
        return self.permission_required + self.get_object().extra_change_perms_str_tuple

    # Cache this method, as it will be called multiple times
    # (`maxsize` need only be 1, since the cached value is not supposed to last longer than each request)
    @lru_cache(maxsize=1)
    def get_object(self, queryset=None):
        return super().get_object()

    def get_form_class(self):
        # Allow editing HTML source code if this permission is required by the view
        # (not if the user has the permission or not, as that is handled by `PermissionRequiredMixin`):
        if 'internal.can_change_rich_text_source' in self.get_permission_required():
            return EditSourceContentBoxForm
        return super().get_form_class()

    def get_form_title(self):
        return self._get_page_title(_("Change"))

    def _get_page_title(self, prefixed_verb: str = None):
        prefix = f"{prefixed_verb} " if prefixed_verb else ""
        url_path = urlparse(self.get_success_url()).path
        html_text = f"{prefix}<code>{self.object.url_name}</code> (<code>{url_path}</code>)"
        return mark_safe(html_text)

    def get_back_button_link(self):
        return self.get_success_url()

    def get_back_button_text(self):
        return self._get_page_title(pgettext("view page", "View"))

    def get_success_url(self):
        return self._absolute_url(self.object)
