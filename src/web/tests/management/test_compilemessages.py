import io
import re
from pathlib import Path
from unittest import TestCase as StandardTestCase

from django.core import management

from web.tests.management.test_makemessages import (
    LocaleFileType,
    get_project_locale_files,
)


class CompilessagesTests(StandardTestCase):
    def test_mo_files_are_up_to_date(self):
        before_contents = self.get_mo_file_contents()

        # For some reason, changes in the `.po` files are often not reflected in
        # the `.mo` files when running `compilemessages` - unless the `.mo` files
        # are deleted first, in which case they seem to be consistently updated
        self.delete_mo_files()
        management.call_command("compilemessages")

        after_contents = self.get_mo_file_contents()

        if after_contents != before_contents:
            self.fail(
                f"\n{'#' * 52}"
                "\n### One or more of the `.mo` files are outdated! ###"
                "\n### Run `make compilemessages` to fix this.      ###"
                f"\n{'#' * 52}"
            )

        self._test_compilemessages_only_processes_our_mo_files()

    @staticmethod
    def get_mo_file_contents() -> dict[Path, bytes]:
        return {
            path: path.read_bytes()
            for path in get_project_locale_files(LocaleFileType.MO)
        }

    @staticmethod
    def delete_mo_files():
        for path in get_project_locale_files(LocaleFileType.MO):
            path.unlink()

    def _test_compilemessages_only_processes_our_mo_files(self):
        """Test that the ``compilemessages`` command only processes ``.mo`` files inside
        our project apps (see the comment above
        ``web.management.commands.makemessages.Command.DEFAULT_IGNORED_DIRS``).

        NOTE: This should only be called after confirming that the ``.mo`` files are up
              to date, as that's assumed to be the case when checking the command
              output.
        """
        out = io.StringIO()
        err = io.StringIO()
        management.call_command("compilemessages", stdout=out, stderr=err)
        output = out.getvalue().strip()
        self.assertFalse(err.getvalue().strip())

        # Example line: `File “path/to/file.po” is already compiled and up to date.`
        file_paths = {
            Path(path) for path in re.findall(r"[\w\s]*“(.+)”[\w\s]*", output)
        }
        self.assertSetEqual(
            file_paths, set(get_project_locale_files(LocaleFileType.PO))
        )
