from ckeditor.fields import RichTextField
from django.db import models

class Tool(models.Model):
    title = models.CharField(max_length=100, verbose_name=('Title'),)
    image = models.ImageField(verbose_name=('Image'), blank=True,)
    content = RichTextField()

# Create your models here.

