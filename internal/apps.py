from django.apps import AppConfig


class InternalConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'internal'

    # noinspection PyUnresolvedReferences
    def ready(self):
        # Import the signals here, so that they're registered/connected when the app starts
        from . import signals
