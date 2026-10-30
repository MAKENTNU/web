import subprocess
import sys
from unittest import TestCase as StandardTestCase


class ShellPlusTests(StandardTestCase):
    def test__shell_plus__starts_successfully(self):
        result = subprocess.run(  # noqa: PLW1510
            [sys.executable, "manage.py", "shell_plus", "--command=pass"],
            capture_output=True,
        )
        error_output = result.stderr.decode().strip()
        self.assertEqual(error_output, "")
        result.check_returncode()
