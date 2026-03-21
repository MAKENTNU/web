from enum import StrEnum
from pathlib import Path
from unittest import TestCase as StandardTestCase

from django.conf import settings
from django.core import management


class LocaleFileType(StrEnum):
    PO = ".po"
    MO = ".mo"


def get_project_locale_files(file_type: LocaleFileType) -> list[Path]:
    return [
        file_path
        for dir_path in settings.LOCALE_PATHS
        for file_path in Path(dir_path).rglob(f"*{file_type}")
    ]


class MakemessagesTests(StandardTestCase):
    def test_po_files_are_up_to_date(self):
        before_contents = self.get_po_file_contents()
        management.call_command("makemessages", all=True)
        management.call_command("makemessages", all=True, domain="djangojs")
        after_contents = self.get_po_file_contents()

        if after_contents != before_contents:
            self.fail(
                f"\n{'#' * 52}"
                "\n### One or more of the `.po` files are outdated! ###"
                "\n### Run `make makemessages-all` to fix this.     ###"
                f"\n{'#' * 52}"
            )

    @classmethod
    def get_po_file_contents(cls) -> dict[Path, str]:
        def get_contents(path: Path) -> str:
            contents = path.read_text(encoding="utf-8")
            # Remove the `POT-Creation-Date:` line, as it can change even if no other
            # parts of the contents have changed, leading to false test failures
            contents = "\n".join(
                line
                for line in contents.splitlines()
                if not line.startswith('"POT-Creation-Date:')
            )
            return contents

        return {
            path: get_contents(path)
            for path in get_project_locale_files(LocaleFileType.PO)
        }
