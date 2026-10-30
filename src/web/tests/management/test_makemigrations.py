import io
from unittest import TestCase as StandardTestCase

from django.core import management


class MakemigrationsTests(StandardTestCase):
    def test__makemigrations__detects_no_changes(self):
        out = io.StringIO()
        err = io.StringIO()
        management.call_command("makemigrations", dry_run=True, stdout=out, stderr=err)
        self.assertEqual(err.getvalue().strip(), "")
        if out.getvalue().strip() != "No changes detected":
            self.fail(
                f"\n{'#' * 63}"
                "\n### There are changes in the code that are not reflected in ###"
                "\n### the migrations! Run `make makemigrations` to fix this.  ###"
                f"\n{'#' * 63}"
            )
