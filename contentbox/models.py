from ckeditor.fields import RichTextField
from django.db import models

class ContentBox(models.Model):
    title = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Tittel',
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
