from django.apps import apps
from django.db import models
from django.db.models.signals import post_save

from .storage import UploadToUtils


def connect():
    # Connect to all models whose fields might use `UploadToUtils`'s method as their `upload_to` argument
    for model in apps.get_models():
        if model_has_file_field(model):
            post_save.connect(UploadToUtils.rename_files_of_created_instances, sender=model)
            continue


def model_has_file_field(model: models.Model):
    for field in model._meta.get_fields():
        if isinstance(field, models.FileField):
            return True
    return False
