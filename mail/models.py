from django.db import models
from django.utils.translation import gettext_lazy as _

from web.multilingual.database import MultiLingualTextField, MultiLingualRichTextUploadingField


class Email(models.Model):
    subject = MultiLingualTextField(
        max_length=100,
        verbose_name=_("Subject"),
    )
    message = MultiLingualRichTextUploadingField(
        verbose_name=_("Message"),
    )

    class Meta:
        permissions = (
            ("can_send_mail", "Can send email"),
        )

    def __str__(self):
        return str(self.subject)
