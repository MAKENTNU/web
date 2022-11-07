from collections.abc import Sequence
from html.entities import html5

from django.db.models import QuerySet
from django.utils.html import escape, format_html, format_html_join
from django.utils.safestring import mark_safe
from django_hosts import reverse_host


def _should_include_escape_entry(unicode_character: str, named_character: str):
    # Some of the named characters appear both with and without a trailing semicolon;
    # see https://docs.python.org/3.9/library/html.entities.html#html.entities.html5
    if not named_character.endswith(";"):
        return False

    if len(unicode_character) != 1:
        return False
    # The character should be escaped (and therefore included in the dict) if it's not ASCII.
    # Might have to tweak the condition below, e.g. by checking if the character is part of `string.printable` instead.
    should_escape = ord(unicode_character) >= 128
    return should_escape


ESCAPE_UNICODE_TO_HTML5 = {
    unicode_character: f"&{named_character}"
    for named_character, unicode_character in html5.items()
    if _should_include_escape_entry(unicode_character, named_character)
}


def escape_to_named_characters(string: str):
    return "".join(ESCAPE_UNICODE_TO_HTML5.get(c, c) for c in string)


def block_join(object_collection: Sequence | QuerySet, sep="<b>&bull;</b>", multiline=True):
    if len(object_collection) == 0:
        return ""

    tag = '<div style="display: inline-block; white-space: nowrap;">'
    if multiline:
        return format_html_join(
            mark_safe("<br>"), f"{tag}{sep}" + " {}</div>",
            ((str(obj),) for obj in object_collection)
        )
    else:
        if len(object_collection) > 1:
            everything_except_first = format_html_join(
                "", f" {tag}{sep}" + " {}</div>",
                ((str(obj),) for obj in object_collection[1:])
            )
        else:
            everything_except_first = ""
        return mark_safe(tag) + escape(object_collection[0]) + mark_safe("</div>") + everything_except_first


def tag_media_img(media_img_url: str, *, url_host_name='', alt_text: str, max_size="50px"):
    if url_host_name:
        media_img_url = f"//{reverse_host(url_host_name)}{media_img_url}"
    return format_html('<img src="{}" style="max-width: {}; max-height: {};" alt="{}"/>',
                       media_img_url, max_size, max_size, alt_text)
