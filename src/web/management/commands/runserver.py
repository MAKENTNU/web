import re
import traceback

from daphne.management.commands import runserver
from django.conf import settings


class Command(runserver.Command):
    """
    Overrides the ``runserver`` management command.
    It's currently extending ``daphne``'s command, as it's the one we would normally be using.

    This requires that ``web.apps.WebConfig`` is listed before other apps that override ``runserver``, in the ``INSTALLED_APPS`` setting.
    """

    def inner_run(self, *args, **options):
        if not settings.DEBUG:
            super().inner_run(*args, **options)

        addr_regex = r"(?:localhost|127\.0\.0\.1|0\.0\.0\.0)"
        dev_server_addr_regex = re.compile(
            rf"(Starting .*development server at https?://)({addr_regex}):(\d+)",
            re.IGNORECASE,
        )
        original_write_func = self.stdout.write

        def write(msg="", *args_, **kwargs_):
            regex_match = dev_server_addr_regex.search(msg)
            if regex_match:
                parent_host = settings.PARENT_HOST
                # noinspection PyBroadException
                try:
                    prefix, dev_server_prefix_str, _addr, port, suffix = (
                        dev_server_addr_regex.split(msg)
                    )
                    dev_host_addr = parent_host[: parent_host.rindex(":")]
                    msg = (
                        f"{prefix}{dev_server_prefix_str}{dev_host_addr}:{port}{suffix}"
                    )
                except Exception:
                    self.stderr.write(
                        f"Error while parsing development server address string:"
                    )
                    self.stderr.write(traceback.format_exc())
                # Reset the write function, which prevents this function from unnecessarily doing regex matching
                self.stdout.write = original_write_func

            original_write_func(msg=msg, *args_, **kwargs_)

        self.stdout.write = write
        super().inner_run(*args, **options)
