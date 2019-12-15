from django.conf.urls import url as durl
from django.db import models
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
    def url(title):
        return durl(r'%s/$' % title, DisplayContentBoxView.as_view(title=title), name=title)

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
