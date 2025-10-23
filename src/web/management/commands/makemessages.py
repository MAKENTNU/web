import re
from pathlib import Path
from typing import Final

from django.conf import settings
from django.core.management.commands import makemessages


class Command(makemessages.Command):
    # Remove leading `./` as well, in case it ever happens to be generated (see comment above `write_po_file()` for context)
    PATH_PREFIX_REGEX: Final = re.compile(r" \.[\\/]")
    PATH_PREFIX_REPLACEMENT: Final = " "

    # Ignore all top-level directories that are not the `BASE_DIR`
    DEFAULT_IGNORED_DIRS: Final = [
        path.name
        for path in settings.REPO_DIR.iterdir()
        if path.is_dir() and path != settings.BASE_DIR
    ]
    IGNORED_DIRS_HELP_SUFFIX: Final = (
        "\n\nIf no --ignore options are provided, the following directories are ignored:"
        f" [{', '.join(DEFAULT_IGNORED_DIRS)}]."
    )

    help = f"{makemessages.Command.help}{IGNORED_DIRS_HELP_SUFFIX}"

    def execute(self, *args, **options):
        ignore_patterns: list[str] = options['ignore_patterns']
        if len(ignore_patterns) == 0:
            ignore_patterns.extend(self.get_default_ignore_patterns())

        return super().execute(*args, **options)

    # On Windows, it seems like the `.po` files consistently have their file location comments formatted with
    # backslashes (\) instead of forward slashes (/) - which is the standard file path format on Windows - and
    # a leading `.\` path prefix.
    # The code below converts those comments to the format generated on Linux (forward slashes and no leading `.\`),
    # to ensure that the command output is not dependent on each developer's operating system.
    def write_po_file(self, potfile, locale):
        super().write_po_file(potfile=potfile, locale=locale)

        # Based on https://github.com/django/django/blob/4.1.7/django/core/management/commands/makemessages.py#L683-L685
        locale_dir = Path(potfile).parent / locale / 'LC_MESSAGES'
        po_file = locale_dir / f'{self.domain}.po'

        original_po_file_contents = po_file.read_text(encoding='utf-8')
        po_file_lines = original_po_file_contents.splitlines(keepends=True)
        for i, line in enumerate(po_file_lines):
            if line.startswith("#:"):
                po_file_lines[i] = (
                    self.PATH_PREFIX_REGEX.sub(self.PATH_PREFIX_REPLACEMENT, line)
                    .replace("\\", "/")
                )

        new_po_file_contents = "".join(po_file_lines)
        if new_po_file_contents != original_po_file_contents:
            # Based on https://github.com/django/django/blob/4.1.7/django/core/management/commands/makemessages.py#L707-L708
            with open(po_file, 'w', encoding='utf-8') as fp:
                fp.write(new_po_file_contents)

    @classmethod
    def get_default_ignore_patterns(cls) -> list[str]:
        patterns = []
        for dir_name in cls.DEFAULT_IGNORED_DIRS:
            glob_path = Path(f"{dir_name}/**")
            patterns.append(str(glob_path))

        return patterns
