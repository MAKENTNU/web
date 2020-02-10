from django.conf import settings
from django.contrib import messages
from django.core.files.uploadhandler import StopUpload, TemporaryFileUploadHandler
from django.template.defaultfilters import filesizeformat
from django.utils.translation import ugettext_lazy as _


# Code modified and copied from https://github.com/django/django/blob/d6eaf7c0183cd04b78f2a55e1d60bb7e59598310/tests/file_uploads/uploadhandler.py#L8
class ThrottledUploadHandler(TemporaryFileUploadHandler):

    def __init__(self, request=None):
        super().__init__(request)
        self.total_upload = 0

    def receive_data_chunk(self, raw_data, start):
        self.total_upload += len(raw_data)
        if self.total_upload > settings.MAX_UPLOADED_IMAGE_SIZE:
            messages.error(self.request,
                           _("Uploaded files cannot be larger than {size}").format(size=filesizeformat(settings.MAX_UPLOADED_IMAGE_SIZE)))
            raise StopUpload(connection_reset=True)

        return super().receive_data_chunk(raw_data, start)
