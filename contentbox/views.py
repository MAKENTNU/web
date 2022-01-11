from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import path, reverse
from django.views.generic import DetailView, UpdateView

from .models import ContentBox


class DisplayContentBoxView(DetailView):
    model = ContentBox
    template_name = 'contentbox/display.html'
    context_object_name = 'contentbox'

    # The value of this field is set when calling the view's `as_view()` method
    url_name = None

    def get_object(self, queryset=None):
        contentbox, _created = ContentBox.objects.get_or_create(url_name=self.url_name)
        return contentbox

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


class EditContentBoxView(PermissionRequiredMixin, UpdateView):
    permission_required = ('contentbox.change_contentbox',)
    model = ContentBox
    fields = ('title', 'content',)
    template_name = 'contentbox/edit.html'

    def get_success_url(self):
        return reverse(self.object.url_name)
