import sys
from io import BytesIO
from typing import Union

from PIL import Image
from django import forms
from django.core.files import File
from django.core.files.uploadedfile import InMemoryUploadedFile, TemporaryUploadedFile
from django.db.models.fields.files import ImageFieldFile

from util.file_utils import file_contents_equal, filenames_equal
from util.logging_utils import get_request_logger


class CompressedImageField(forms.ImageField):
    """
    An image form field that compresses images during cleaning, by reducing the quality of the image.
    This only applies to JPEG images; images of all other formats will be left unchanged.
    """

    def clean(self, data: Union[InMemoryUploadedFile, bool, None], initial: ImageFieldFile = None):
        cleaned_data: Union[ImageFieldFile, InMemoryUploadedFile, TemporaryUploadedFile, bool, None] = super().clean(data, initial=initial)
        if data and cleaned_data:
            if initial and file_contents_equal(cleaned_data, initial):
                if not filenames_equal(cleaned_data, initial):
                    # Return the cleaned data, so that the image will get the name of the uploaded file
                    return cleaned_data
                # Don't change the field at all (unlike returning `False`, which would clear the image field and delete the existing file)
                return None

            try:
                with Image.open(cleaned_data) as pillow_image:
                    if pillow_image.format == 'JPEG':

                        if isinstance(cleaned_data, InMemoryUploadedFile):
                            output = BytesIO()
                            self._save_reduced_image(pillow_image, output)
                            return InMemoryUploadedFile(
                                output, cleaned_data.field_name, cleaned_data.name,
                                cleaned_data.content_type, sys.getsizeof(output), cleaned_data.charset,
                            )
                        elif isinstance(cleaned_data, TemporaryUploadedFile):
                            new_file = TemporaryUploadedFile(
                                cleaned_data.name, cleaned_data.content_type, 0, cleaned_data.charset, cleaned_data.content_type_extra,
                            )
                            self._save_reduced_image(pillow_image, new_file)
                            return new_file
                        else:
                            raise forms.ValidationError(f"Unexpected type of uploaded file: {type(cleaned_data)}")

            except IOError as e:
                # Pillow (PIL) will throw an IOError if it cannot open the image, or does not support the given format
                get_request_logger().exception(e)

        return cleaned_data

    @staticmethod
    def _save_reduced_image(image: Image, file: Union[BytesIO, File]):
        image.save(file, format='JPEG', quality=90)
