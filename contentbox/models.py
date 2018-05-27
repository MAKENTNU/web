from ckeditor.fields import RichTextField
from django.utils.translation import gettext_lazy as _
from django.conf.urls import url as durl
from django.db import models
from django.views.generic import TemplateView


class ContentBox(models.Model):
    title = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_('Title'),
    )
    content = RichTextField()

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


class DisplayContentBoxView(TemplateView):
    template_name = 'contentbox/display.html'
    title = ''

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'contentbox': ContentBox.get(self.title)
        })
        return context
