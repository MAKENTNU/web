import sys
from io import BytesIO

from PIL import Image
from django.core.files.uploadedfile import InMemoryUploadedFile

from util.logging_utils import get_request_logger


class PlaceholderName:

    def save(self, **kwargs):
        """
        Override of save, to change all JPEG images to have quality 90. This greatly reduces the size of JPEG images,
        while resulting in non to very minuscule reduction in quality. In almost all cases, the possible reduction in
        quality will not be visible to the naked eye.
        """
        # Only check the image if there is actually an image
        if self.image:
            # PIL will throw an IO error if it cannot open the image, or does not support the given format
            try:
                image = Image.open(self.image)
                if image.format == "JPEG":
                    output = BytesIO()
                    image.save(output, format="JPEG", quality=90)
                    output.seek(0)

                    self.image = InMemoryUploadedFile(output, "ImageField", self.image.name, "image/jpeg",
                                                      sys.getsizeof(output), None)
                # Should not close image, as Django uses the image and closes it by default
            except IOError as e:
                get_request_logger().exception(e)

        super().save(**kwargs)
