import re
from pathlib import Path

from django.conf import settings
from django.core.management.commands import makemessages


class Command(makemessages.Command):
    help = (
        f"{makemessages.Command.help}"
        "\n\nIf no --ignore options are provided, it's by default set to the names of all top-level directories under the 'REPO_DIR' setting,"
        " except for the Django source directory (the 'BASE_DIR' setting)."
    )

    # Remove leading `./` as well, in case it ever happens to be generated (see comment above `write_po_file()` for context)
    _path_prefix_regex = re.compile(r" \.[\\/]")
    _path_prefix_replacement = " "

    def execute(self, *args, **options):
        ignore_patterns = options['ignore_patterns']
        if not ignore_patterns:
            # Ignore all top-level directories that are not the `BASE_DIR`
            for path in settings.REPO_DIR.iterdir():
                if path.is_dir() and path != settings.BASE_DIR:
                    ignore_patterns.append(path.name)

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
                    self._path_prefix_regex.sub(self._path_prefix_replacement, line)
                    .replace("\\", "/")
                )

        new_po_file_contents = "".join(po_file_lines)
        if new_po_file_contents != original_po_file_contents:
            # Based on https://github.com/django/django/blob/4.1.7/django/core/management/commands/makemessages.py#L707-L708
            with open(po_file, 'w', encoding='utf-8') as fp:
                fp.write(new_po_file_contents)
