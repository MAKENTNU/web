import re
import traceback

from channels.management.commands import runserver
from django.conf import settings


class Command(runserver.Command):
    """
    Overrides the ``runserver`` management command.
    It's currently extending ``channels``' command, as it's the one we would normally be using.

    This requires that the ``web`` app is listed before other apps that override ``runserver``, in the ``INSTALLED_APPS`` setting.
    """

    def inner_run(self, *args, **options):
        if not settings.DEBUG:
            super().inner_run(*args, **options)

        addr_regex = r"(?:127\.0\.0\.1|localhost)"
        dev_server_addr_regex = re.compile(
            rf"(Starting .*development server at https?://)({addr_regex}):(\d+)",
            re.IGNORECASE
        )
        original_write_func = self.stdout.write

        def write(msg="", *args_, **kwargs_):
            regex_match = dev_server_addr_regex.search(msg)
            if regex_match:
                # noinspection PyBroadException
                try:
                    prefix, dev_server_prefix_str, _addr, port, suffix = dev_server_addr_regex.split(msg)
                    dev_host_addr = settings.PARENT_HOST[:settings.PARENT_HOST.rindex(':')]
                    msg = f"{prefix}{dev_server_prefix_str}{dev_host_addr}:{port}{suffix}"
                except Exception:
                    self.stderr.write(f"Error while parsing development server address string:")
                    self.stderr.write(traceback.format_exc())
                # Reset the write function, which prevents this function from unnecessarily doing regex matching
                self.stdout.write = original_write_func

            original_write_func(msg=msg, *args_, **kwargs_)

        self.stdout.write = write
        super().inner_run(*args, **options)
