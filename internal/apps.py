from django.apps import AppConfig


class InternalConfig(AppConfig):
    name = 'internal'

    def ready(self):
        # noinspection PyUnresolvedReferences
        from . import signals
