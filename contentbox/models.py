from django.db import models
from django.urls import path as django_path
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from web.multilingual.database import MultiLingualRichTextUploadingField


class ContentBox(models.Model):
    title = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_('Title'),
    )
    content = MultiLingualRichTextUploadingField()

    def __str__(self):
        return self.title

    @staticmethod
    def get(title):
        try:
            return ContentBox.objects.get(title=title)
        except ContentBox.DoesNotExist:
            return ContentBox.objects.create(title=title)

    @staticmethod
    def path(title):
        return django_path(f'{title}/', DisplayContentBoxView.as_view(title=title), name=title)

    @staticmethod
    def multi_path(title, alt_url1, *other_alt_urls) -> tuple:
        alt_urls = (alt_url1, *other_alt_urls)
        return (
            django_path(f'{title}/', DisplayContentBoxView.as_view(title=title), name=title),
            *(django_path(f'{url}/', DisplayContentBoxView.as_view(title=title)) for url in alt_urls),
        )

    class Meta:
        permissions = (
            ("can_upload_image", "Can upload image for CKEditor"),
            ("can_browse_image", "Can brows image in CKEditor"),
        )


class DisplayContentBoxView(TemplateView):
    template_name = 'contentbox/display.html'
    title = ''

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'contentbox': ContentBox.get(self.title),
        })
        return context
