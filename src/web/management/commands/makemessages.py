from django.conf import settings
from django.core.management.commands import makemessages


class Command(makemessages.Command):
    help = (
        f"{makemessages.Command.help}"
        "\n\nIf no --ignore options are provided, it's by default set to the names of all top-level directories under the 'REPO_DIR' setting,"
        " except for the Django source directory (the 'BASE_DIR' setting)."
    )

    def execute(self, *args, **options):
        ignore_patterns = options['ignore_patterns']
        if not ignore_patterns:
            # Ignore all top-level directories that are not the `BASE_DIR`
            for path in settings.REPO_DIR.iterdir():
                if path.is_dir() and path != settings.BASE_DIR:
                    ignore_patterns.append(path.name)

        return super().execute(*args, **options)
