from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import path, reverse
from django.views.generic import DetailView, UpdateView

from .models import ContentBox


class DisplayContentBoxView(DetailView):
    model = ContentBox
    template_name = 'contentbox/display.html'
    context_object_name = 'contentbox'
    title = ""

    def get_object(self, queryset=None):
        contentbox, _created = ContentBox.objects.get_or_create(title=self.title)
        return contentbox

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


class EditContentBoxView(PermissionRequiredMixin, UpdateView):
    permission_required = ('contentbox.change_contentbox',)
    model = ContentBox
    fields = ('content',)
    template_name = 'contentbox/edit.html'

    def get_success_url(self):
        return reverse(self.object.title)
