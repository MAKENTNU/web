from django.utils.html import format_html
from django_hosts import reverse_host


def tag_media_img(media_img_url: str, *, url_host_name='', alt_text: str, max_size="50px"):
    if url_host_name:
        media_img_url = f"//{reverse_host(url_host_name)}{media_img_url}"
    return format_html('<img src="{}" style="max-width: {}; max-height: {};" alt="{}"/>',
                       media_img_url, max_size, max_size, alt_text)
