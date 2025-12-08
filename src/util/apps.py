from django.apps import AppConfig


class UtilConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "util"

    def ready(self):
        # Importing models (which is done in the `signals` module) should not be done in the global scope,
        # as it would have caused an `AppRegistryNotReady` error
        from . import signals

        # Register / connect to the signals here when the app starts
        signals.connect()
