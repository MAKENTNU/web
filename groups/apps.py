from django.apps import AppConfig

from . import signals


class GroupsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'groups'

    def ready(self):
        # Register / connect to the signals here when the app starts
        signals.connect()
