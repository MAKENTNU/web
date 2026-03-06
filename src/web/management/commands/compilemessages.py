from django.core.management.commands import compilemessages

from web.management.commands.makemessages import Command as MakeMessagesCommand


class Command(compilemessages.Command):
    """A custom override of the ``compilemessages`` command.

    Differences from the standard command:

    * Ignores files within the top-level directories that don't contain our project's
      Python code.
    """

    help = (
        f"{compilemessages.Command.help}{MakeMessagesCommand.IGNORED_DIRS_HELP_SUFFIX}"
    )

    def execute(self, *args, **options):
        ignore_patterns: list[str] = options["ignore_patterns"]
        if len(ignore_patterns) == 0:
            # (This is mainly to ignore venv folders, which often contain hundreds of
            # `.mo` files that this command will happily start churning through if not
            # ignored)
            ignore_patterns.extend(MakeMessagesCommand.get_default_ignore_patterns())

        return super().execute(*args, **options)
