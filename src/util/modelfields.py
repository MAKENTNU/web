from django.db import models

from . import formfields


class CompressedImageField(models.ImageField):
    """
    An image field that compresses images before saving them to the filesystem;
    see the documentation of ``formfields.CompressedImageField`` for details.
    """

    def formfield(self, **kwargs):
        return super().formfield(
            **{
                "form_class": formfields.CompressedImageField,
                **kwargs,
            }
        )
