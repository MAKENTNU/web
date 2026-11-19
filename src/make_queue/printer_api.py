"""
Communication with the 3D printers that run `Klipper <https://www.klipper3d.org/>`_,
through their `Moonraker <https://moonraker.readthedocs.io/en/latest/>`_ API server.
This is the same API that the printers' web interfaces (e.g. Mainsail or Fluidd) use,
and it's documented at https://moonraker.readthedocs.io/en/latest/web_api/.

The printers are not reachable from the internet; the server reaches them through
`Tailscale <https://tailscale.com/kb/1151/what-is-tailscale>`_, which gives every
device an IP address in the ``100.64.0.0/10`` range, and (when
`MagicDNS <https://tailscale.com/kb/1081/magicdns>`_ is enabled) a hostname like
``printer-1`` or ``printer-1.tail1234.ts.net``.
"""

import io
import ipaddress
import re
import socket
from typing import Final

import requests
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
from django.utils.translation import gettext_lazy as _
from urllib3.fields import RequestField
from urllib3.filepost import choose_boundary, encode_multipart_formdata

# The IPv4 range that Tailscale assigns addresses from (the "Carrier-Grade NAT" range).
# It's not considered private by `ipaddress`, so it must be allowed explicitly.
# See https://tailscale.com/kb/1015/100.x-addresses
TAILSCALE_IPV4_NETWORK: Final = ipaddress.ip_network("100.64.0.0/10")

# A hostname consisting of one or more dot-separated labels (see RFC 1123), e.g.
# `printer-1` or `printer-1.tail1234.ts.net`
HOSTNAME_REGEX: Final = re.compile(
    r"^(?=.{1,253}$)[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?(\.[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?)*$",
    re.IGNORECASE,
)

# The printer's states (`print_stats.state`) in which a new file shouldn't be uploaded.
# All states are listed at
# https://moonraker.readthedocs.io/en/latest/printer_objects/#print_stats
BUSY_PRINT_STATES: Final = {"printing", "paused"}
# used when the printer can't be reached
OFFLINE_STATE: Final = "offline"

# How large a share of the (non-empty) lines at the start of a file must look like
# G-code for the file to be accepted
MIN_VALID_GCODE_LINE_RATIO: Final = 0.8


class PrinterError(Exception):
    """
    Raised when communicating with a printer fails.

    ``user_message`` is safe to show to users, while the exception's string (passed
    as the first argument) can contain technical details meant for the logs.
    """

    def __init__(self, log_message: str, *, user_message: str):
        super().__init__(log_message)
        self.user_message = user_message


def validate_printer_address(address: str):
    """Validator for the address field of a machine: an IP address or a hostname."""
    try:
        ipaddress.ip_address(address)
    except ValueError:
        if not HOSTNAME_REGEX.match(address):
            raise ValidationError(
                _("Enter a valid IP address or hostname."), code="invalid"
            ) from None


def is_allowed_printer_ip(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    """
    Only allow addresses on local networks or on the Tailscale network, so that the
    server can't be made to send requests to arbitrary hosts on the internet, nor to
    services on the server itself (loopback) or to cloud metadata services
    (link-local, e.g. ``169.254.169.254``).

    Tailscale's IPv6 addresses (``fd7a:115c:a1e0::/48``) are private, so they're
    allowed through ``is_private``.
    """
    if ip.is_loopback or ip.is_link_local:
        return False
    return ip.is_private or ip in TAILSCALE_IPV4_NETWORK


def resolve_printer_address(address: str) -> str:
    """
    Returns the IP address that ``address`` (an IP address or hostname) points to.

    The returned IP is the one that should be connected to, instead of passing the
    hostname on to ``requests``; otherwise, the hostname could resolve to a different
    (disallowed) IP between being checked here and being connected to.
    """
    if not address:
        raise PrinterError(
            "The machine has no printer address.",
            user_message=_("The printer's address has not been configured."),
        )

    try:
        ips = [ipaddress.ip_address(address)]
    except ValueError:
        try:
            address_infos = socket.getaddrinfo(address, None, type=socket.SOCK_STREAM)
        except OSError as e:
            raise PrinterError(
                f"Could not resolve the printer address {address!r}: {e}",
                user_message=_("Could not find the printer on the network."),
            ) from e
        # The first element of the `sockaddr` tuple is the IP address; IPv6 addresses
        # can have a `%<interface>` suffix, which `ip_address()` doesn't accept
        ips = [
            ipaddress.ip_address(sockaddr[0].split("%")[0])
            for *_rest, sockaddr in address_infos
        ]

    if not all(is_allowed_printer_ip(ip) for ip in ips):
        raise PrinterError(
            f"The printer address {address!r} resolves to a disallowed IP: {ips}",
            user_message=_("The printer's address is not allowed."),
        )
    return str(ips[0])


def get_base_url(address: str) -> str:
    ip = resolve_printer_address(address)
    # IPv6 addresses must be enclosed in brackets in URLs
    host = f"[{ip}]" if ":" in ip else ip
    return f"http://{host}"


def get_print_state(address: str) -> str:
    """
    Returns the state of the printer's current print job, e.g. ``"standby"`` or
    ``"printing"``, or :data:`OFFLINE_STATE` if the printer can't be reached.

    """
    try:
        response = requests.get(
            f"{get_base_url(address)}/printer/objects/query",
            params={"print_stats": "state"},
            timeout=5,
        )
        response.raise_for_status()
        return response.json()["result"]["status"]["print_stats"]["state"]
    # `RequestException`: the printer couldn't be reached, or didn't return JSON;
    # `KeyError`/`TypeError`: the JSON didn't have the expected structure
    except (PrinterError, requests.RequestException, KeyError, TypeError):
        return OFFLINE_STATE


def upload_gcode(address: str, file: UploadedFile, *, filename: str):
    """
    Uploads ``file`` to the printer's G-code folder, overwriting any existing file with
    the same name.

    See https://moonraker.readthedocs.io/en/latest/web_api/#file-upload

    :raises PrinterError: if the upload failed.
    """
    url = f"{get_base_url(address)}/server/files/upload"
    body = StreamingMultipartBody(
        {"root": "gcodes", "path": ""}, file_field="file", file=file, filename=filename
    )
    try:
        response = requests.post(
            url,
            data=body,
            headers={"Content-Type": body.content_type},
            # As the body is streamed, the read timeout applies to sending each block
            # and to waiting for the response - not to the whole upload
            timeout=(5, 120),
        )
    except requests.Timeout as e:
        raise PrinterError(
            f"Uploading G-code to {url} timed out: {e}",
            user_message=_(
                "The printer took too long to respond. Check whether the file appeared"
                " on the printer before trying again."
            ),
        ) from e
    except requests.RequestException as e:
        raise PrinterError(
            f"Uploading G-code to {url} failed: {e}",
            user_message=_("Could not connect to the printer."),
        ) from e

    if not response.ok:
        raise PrinterError(
            f"{url} rejected the G-code upload with status {response.status_code}:"
            f" {response.text[:1000]}",
            user_message=_("The printer rejected the file (status %(code)s).")
            % {"code": response.status_code},
        )


def looks_like_gcode(file: UploadedFile) -> bool:
    """
    A quick sanity check that the start of ``file`` looks like G-code, to stop users
    from accidentally uploading e.g. an STL file that has been renamed to ``.gcode``.

    G-code consists of one command per line, where each command starts with a letter
    that says which kind of command it is (see https://reprap.org/wiki/G-code), and
    comments start with ``;``. The prefixes accepted here are the ones that slicers
    write to the start of their files: ``G`` (movement etc.), ``M`` (miscellaneous,
    e.g. temperatures), ``T`` (tool selection), ``N`` (line numbers) and ``;``.
    As some slicers write other things too (e.g. Klipper macros like
    ``EXCLUDE_OBJECT_DEFINE``), only :data:`MIN_VALID_GCODE_LINE_RATIO` of the lines
    have to match.
    """
    try:
        file.seek(0)
        chunk = file.read(8192)
        file.seek(0)
    # `ValueError` is raised if the file has been closed
    except (OSError, ValueError):
        return False

    if isinstance(chunk, bytes):
        chunk = chunk.decode("utf-8", errors="ignore")

    lines = [line.strip() for line in chunk.splitlines() if line.strip()]
    if not lines:
        return False

    valid_prefixes = ("G", "M", "T", "N", ";")
    valid_count = sum(1 for line in lines if line.upper().startswith(valid_prefixes))
    return valid_count / len(lines) >= MIN_VALID_GCODE_LINE_RATIO


class StreamingMultipartBody:
    """
    A ``multipart/form-data`` request body that reads ``file`` in small blocks while
    it's being sent.

    When passing ``files=...`` to ``requests``, the whole body is built as a single
    ``bytes`` object and sent with one ``socket.sendall()`` call, which means that the
    read timeout limits how long the *entire* upload can take. A large file over a slow
    connection (e.g. Tailscale relaying the traffic) will then time out, even though
    data is flowing the whole time. Passing an instance of this class as ``data``
    instead makes urllib3 send the body in small blocks, so that the timeout only
    applies to each block - i.e. only to a connection that has stalled.
    """

    def __init__(
        self,
        fields: dict[str, str],
        *,
        file_field: str,
        file: UploadedFile,
        filename: str,
    ):
        boundary = choose_boundary()
        self.content_type = f"multipart/form-data; boundary={boundary}"

        file_part = RequestField(file_field, b"", filename=filename)
        file_part.make_multipart(content_type="application/octet-stream")
        # Encode all the fields with an empty file (as the last field), and then send
        # the file's contents between its part headers and the closing boundary
        encoded_fields, _content_type = encode_multipart_formdata(
            [*fields.items(), file_part], boundary=boundary
        )
        closing_boundary = f"\r\n--{boundary}--\r\n".encode()

        file.seek(0)
        self._parts = [
            io.BytesIO(encoded_fields.removesuffix(closing_boundary)),
            file,
            io.BytesIO(closing_boundary),
        ]
        self._length = len(encoded_fields) + file.size

    def __len__(self):
        # Used by `requests` to set the `Content-Length` header
        return self._length

    def read(self, size: int = -1) -> bytes:
        chunks = []
        while self._parts and size != 0:
            chunk = self._parts[0].read(size)
            if not chunk:
                self._parts.pop(0)
                continue
            chunks.append(chunk)
            if size > 0:
                size -= len(chunk)
        return b"".join(chunks)
