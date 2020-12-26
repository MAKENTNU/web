from django.apps import AppConfig

from . import signals


class UtilConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'util'

    def ready(self):
        signals.connect()
