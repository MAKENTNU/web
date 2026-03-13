from pathlib import Path
from typing import Any, Final

from django.conf import settings
from django.core.management.commands import makemessages


class Command(makemessages.Command):
    """A custom override of the ``compilemessages`` command.

    Differences from the standard command:

    * Ignores files that are not part of our project.
    * Prevents ``#:`` comments from being generated.
    """

    # Ignore all top-level directories that are not the `BASE_DIR`, as well as
    # third-party JavaScript libraries
    DEFAULT_IGNORED_DIRS: Final = [
        *(
            path.name
            for path in settings.REPO_DIR.iterdir()
            if path.is_dir() and path != settings.BASE_DIR
        ),
        settings.JS_LIBRARIES_DIR.relative_to(settings.REPO_DIR).as_posix(),
    ]
    IGNORED_DIRS_HELP_SUFFIX: Final = (
        "\n\nIf no --ignore options are provided, the following directories are"
        f" ignored: [{', '.join(DEFAULT_IGNORED_DIRS)}]."
    )

    help = f"{makemessages.Command.help}{IGNORED_DIRS_HELP_SUFFIX}"

    def execute(self, *args, **options):
        ignore_patterns: list[str] = options["ignore_patterns"]
        if len(ignore_patterns) == 0:
            ignore_patterns.extend(self.get_default_ignore_patterns())

        return super().execute(*args, **options)

    def handle(self, *args: Any, **options: Any) -> str | None:
        # The `#:` comments cause merge conflicts too often, so we'd like to omit them
        options["no_location"] = True

        return super().handle(*args, **options)

    @classmethod
    def get_default_ignore_patterns(cls) -> list[str]:
        patterns = []
        for dir_name in cls.DEFAULT_IGNORED_DIRS:
            glob_path = Path(f"{dir_name}/**")
            patterns.append(str(glob_path))

        return patterns
