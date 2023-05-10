from django.conf import settings
from django.core.management import CommandError
from django.core.management.commands import test


class Command(test.Command):
    help = "Discover and run tests in the specified modules or the directory determined by 'settings.TESTS_DIR'."

    # It could be better to override `handle()` instead, but PyCharm's `django_test_manage.py` overrides that method without calling
    # the super class (this class). It doesn't override `execute()`, though, which is why it's overridden here.
    def execute(self, *args, **options):
        relative_tests_dir = settings.TESTS_DIR.relative_to(settings.REPO_DIR)
        if not args:
            args = (str(relative_tests_dir),)
        else:
            relative_dotted_tests_dir = str(relative_tests_dir.as_posix()).replace('/', '.')
            disallowed_prefix = f"{relative_dotted_tests_dir}."
            for arg in args:
                if arg.startswith(disallowed_prefix):
                    raise CommandError(
                        f"Don't prefix the Django project paths with '{relative_dotted_tests_dir}';"
                        f" use paths relative to that directory instead, e.g.: '{arg.removeprefix(disallowed_prefix)}'"
                    )
        return super().execute(*args, **options)
