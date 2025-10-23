from django.core.management.commands import compilemessages

from .makemessages import Command as MakeMessagesCommand


class Command(compilemessages.Command):
    help = f"{compilemessages.Command.help}{MakeMessagesCommand.IGNORED_DIRS_HELP_SUFFIX}"

    def execute(self, *args, **options):
        ignore_patterns: list[str] = options['ignore_patterns']
        if len(ignore_patterns) == 0:
            ignore_patterns.extend(MakeMessagesCommand.get_default_ignore_patterns())

        return super().execute(*args, **options)
