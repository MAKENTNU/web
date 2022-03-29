from django.apps import AppConfig

from . import signals


class InternalConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'internal'

    # noinspection PyUnresolvedReferences
    def ready(self):
        # Register / connect to the signals here when the app starts
        signals.connect()
