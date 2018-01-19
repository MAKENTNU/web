from django.apps import AppConfig


class GroupsConfig(AppConfig):
    name = 'groups'

    def ready(self):
        import groups.signals
