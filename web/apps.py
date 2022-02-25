from django.apps import AppConfig

from . import signals


class WebConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'web'

    def ready(self):
        # Register / connect to the signals here when the app starts
        signals.connect()
