from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import path, reverse
from django.views.generic import TemplateView, UpdateView

from .models import ContentBox


class DisplayContentBoxView(TemplateView):
    template_name = 'contentbox/display.html'
    title = ""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        contentbox, _created = ContentBox.objects.get_or_create(title=self.title)
        context.update({
            'contentbox': contentbox,
        })
        return context

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
    model = ContentBox
    template_name = 'contentbox/edit.html'
    fields = (
        'content',
    )
    permission_required = (
        'contentbox.change_contentbox',
    )

    def get_success_url(self):
        return reverse(self.object.title)
