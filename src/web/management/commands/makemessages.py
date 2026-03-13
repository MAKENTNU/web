from pathlib import Path
from typing import Any, Final

from django.conf import settings
from django.core.management.commands import makemessages


class Command(makemessages.Command):
    """A custom override of the ``compilemessages`` command.

    Differences from the standard command:

    * Ignores files that are not part of our project.
    * Prevents ``#:`` comments from being generated.
    * Prevents ``#, fuzzy`` ``msgstr`` entries from being generated.
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

    msgmerge_options = [
        *makemessages.Command.msgmerge_options,
        # https://www.gnu.org/software/gettext/manual/html_node/msgmerge-Invocation.html#index-_002d_002dno_002dfuzzy_002dmatching_002c-msgmerge-option
        # We don't have any dedicated translators for whom the pre-filled `#, fuzzy`
        # `msgstr`s could help, and since the matching is so often very wrong - which
        # can cause a lot of user confusion if not caught - it's easier for us to just
        # not do any fuzzy matching and instead always generate new, blank translations.
        # This does mean that if you run `makemessages` after changing e.g. one
        # character in an existing message in the code, the previous `msgstr` will be
        # wiped - albeit with the previous `msgid` and `msgstr` commented out with `#~`
        # and moved to the bottom of the `.po` file.
        "--no-fuzzy-matching",
    ]

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
