import re
import secrets
from collections.abc import Callable, Collection
from functools import partial
from pathlib import Path, PurePosixPath

from django.core.files.storage import FileSystemStorage
from django.core.management.base import SystemCheckError
from django.db import models
from django.db.models.fields.files import FieldFile
from sorl.thumbnail import delete as delete_sorl_thumbnail
from sorl.thumbnail.images import ImageFile


# Code based on https://stackoverflow.com/a/4905384
class OverwriteStorage(FileSystemStorage):
    """
    Deletes existing files with the same name when saving.
    WARNING: Before using this storage for a model field, make sure that the names of the files referred to by the field, are always unique.
             Otherwise, files not belonging to the object being saved will be deleted
             if the existing and the uploaded file happen to have the same name.
             This can be done e.g. by the setting the ``upload_to`` option to a function
             which both places the uploaded files in a unique folder (i.e. not used by any other fields or models),
             and makes the filename unique (this can be done using ``UploadToUtils.get_pk_prefixed_filename_func()``).

    [This class was made because ``django-cleanup`` is unable to delete old files before new ones are uploaded,
    which means that when a new file is uploaded with the same name as the old file,
    the newly uploaded file is forced to change name to a unique one, which Django does by suffixing some random characters.]
    """

    def save(self, name, *args, **kwargs):
        if self.exists(name):
            self.delete(name)
            delete_sorl_thumbnail(
                ImageFile(Path(name).as_posix(), storage=self),
                # Should not delete the source file, as this has already been done by `self.delete()` above
                delete_file=False,
            )
        return super().save(name, *args, **kwargs)


class UploadToUtils:
    """
    A collection of utility methods relating to the ``upload_to`` argument of ``FileField`` and subclasses.
    ``get_pk_prefixed_filename_func()`` is the main method intended for use by other apps.
    """
    REPLACEABLE_TOKEN_START = "--replacedByPK"
    REPLACEABLE_TOKEN_MIDDLE_NUM_BYTES = 4
    REPLACEABLE_TOKEN_END = REPLACEABLE_TOKEN_START[::-1]  # reverse the start part of the token
    REPLACEABLE_TOKEN_REGEX = re.compile(rf"({REPLACEABLE_TOKEN_START}-[0-9a-f]+-{REPLACEABLE_TOKEN_END})")

    @classmethod
    def generate_replaceable_token(cls):
        # Produces the same characters as matched by the middle part of the token regex
        token_middle = secrets.token_hex(cls.REPLACEABLE_TOKEN_MIDDLE_NUM_BYTES)
        return f"{cls.REPLACEABLE_TOKEN_START}-{token_middle}-{cls.REPLACEABLE_TOKEN_END}"

    @classmethod
    def get_pk_prefixed_filename_func(cls, upload_to: str | Callable[[models.Model, str], str]):
        """
        Prefixes filenames with the PK (primary key) of each instance.
        When saving a newly created instance (which has no PK), the filename is instead prefixed with a token,
        which is later replaced with the PK right after the instance is saved (this is done through the ``post_save`` signal).

        :param upload_to: the same value as described in
                          https://docs.djangoproject.com/en/stable/ref/models/fields/#django.db.models.FileField.upload_to
        :return: a function which can be passed to the ``upload_to`` argument of a ``FileField`` (or a subclass).
        """
        if not upload_to:
            raise SystemCheckError(
                "The `upload_to` argument must be a string or a callable,"
                " which should ensure that the files of this model field are placed in a folder only used by this specific field."
            )
        return partial(cls._actual_upload_to, upload_to=upload_to)

    @classmethod
    def _actual_upload_to(cls, instance: models.Model, filename: str, *, upload_to: str | Callable[[models.Model, str], str]):
        """This method should only be used by ``get_pk_prefixed_filename_func()``; do not use this method directly."""
        if isinstance(upload_to, str):
            base_path = PurePosixPath(upload_to) / filename
        else:
            base_path = PurePosixPath(upload_to(instance, filename))
        base_filename = base_path.name
        # Remove token if the filename already contains it (for whatever reason)
        if cls.REPLACEABLE_TOKEN_REGEX.search(base_filename):
            first_part, _token, last_part = cls.REPLACEABLE_TOKEN_REGEX.split(base_filename)
            base_filename = f"{first_part}{last_part}"
        # Remove the PK prefix if the filename already has it
        if instance.pk:
            base_filename = base_filename.removeprefix(f"{instance.pk}_")

        prefix = instance.pk or cls.generate_replaceable_token()
        prefixed_filename_path = base_path.with_name(f"{prefix}_{base_filename}")
        return str(prefixed_filename_path)

    @classmethod
    def rename_files_of_created_instances(cls, instance: models.Model, created, raw, update_fields: Collection | None, **kwargs):
        """
        This signal receiver renames the files belonging to ``FileField``s (or subclasses) of model instances when they're created,
        if the filename matches the token regex used by ``get_pk_prefixed_filename_func()``.
        """
        if raw or not created:
            return

        for field in instance._meta.fields:
            # `update_fields` having a value of `None` means that all the fields should be updated
            if (update_fields is not None and field.name not in update_fields
                    or not isinstance(field, models.FileField)):
                continue

            field_value: FieldFile = getattr(instance, field.name)
            old_name = field_value.name
            if not cls.REPLACEABLE_TOKEN_REGEX.search(old_name):
                continue

            first_part, _token, last_part = cls.REPLACEABLE_TOKEN_REGEX.split(old_name)
            new_name = f"{first_part}{instance.pk}{last_part}"

            # Rename the actual file
            old_file_path = Path(field_value.path)
            new_file_path = old_file_path.with_name(Path(new_name).name)
            old_file_path.rename(new_file_path)

            # Save the new filename for the field
            field_value.name = new_name
            instance.save(update_fields=[field.name])
