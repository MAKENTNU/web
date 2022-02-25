from django.apps import AppConfig


class GroupsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'groups'

    # noinspection PyUnresolvedReferences
    def ready(self):
        # Import the signals here, so that they're registered/connected when the app starts
        from . import signals
