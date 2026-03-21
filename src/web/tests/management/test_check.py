import io
from unittest import TestCase as StandardTestCase

from django.core import management


class CheckTests(StandardTestCase):
    def test__check__identifies_no_issues(self):
        out = io.StringIO()
        err = io.StringIO()
        management.call_command("check", fail_level="WARNING", stdout=out, stderr=err)
        self.assertEqual(
            out.getvalue().strip(), "System check identified no issues (0 silenced)."
        )
        self.assertEqual(err.getvalue().strip(), "")
