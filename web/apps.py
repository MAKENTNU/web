from django.apps import AppConfig

from . import signals


class WebConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'web'

    def ready(self):
        signals.connect()
