import re
from fnmatch import fnmatchcase
from io import BytesIO
from typing import Dict, List, Tuple

from django.conf import settings
from django.contrib.staticfiles.storage import HashedFilesMixin, ManifestStaticFilesStorage
from django.http import FileResponse
from django.views.static import serve


# The glob pattern for the files that should have their contents interpolated (as in https://en.wikipedia.org/wiki/String_interpolation)
INTERPOLATION_GLOB_PATTERN = '*.interpolated.*'
INTERPOLATION_PATTERNS = (
    (INTERPOLATION_GLOB_PATTERN, (
        (
            # The strings matching this regex are replaced by the template below
            r"""(?P<matched>\{% static ["'](?P<url>.*?)["'] %\})""",
            # This simply inserts the string matched by the `url` capturing group (defined in the regex above) as it is;
            # when the template is used, the URL in the file has been looked up in the static file manifest, and replaced by its hashed version
            "%(url)s",
        ),
    )),
)


class InterpolatingManifestStaticFilesStorage(ManifestStaticFilesStorage):
    """
    This class extends the functionality of ``ManifestStaticFilesStorage`` by replacing ``static`` tags
    in files whose names end with ``.interpolated`` (not including the extension),  with the path of another static file.

    For example,
    ::
        {% static 'web/img/favicons/android-chrome-192x192.png' %}
    is replaced by
    ::
        /static/web/img/favicons/android-chrome-192x192.edcbcb619832.png
    """
    patterns = (
        *INTERPOLATION_PATTERNS,
        *ManifestStaticFilesStorage.patterns,
    )

    def url_converter(self, name, *args, **kwargs):
        base_converter = super().url_converter(name, *args, **kwargs)
        if not fnmatchcase(name, INTERPOLATION_GLOB_PATTERN):
            return base_converter

        def converter(match_obj: re.Match):
            matches = match_obj.groupdict()
            matched = matches['matched']
            url = matches['url']

            # Prefix the URL with `STATIC_URL`, so that it doesn't get ignored by `base_converter`
            # (see https://github.com/django/django/blob/dc8bb35e39388d41b1f38b6c5d0181224e075f16/django/contrib/staticfiles/storage.py#L184-L187)
            replaced_matched = matched.replace(url, self.get_full_static_url(url))
            return base_converter(match_obj.re.match(replaced_matched))

        return converter

    @staticmethod
    def get_full_static_url(url: str):
        return f"{settings.STATIC_URL}{url}"


class _PureInterpolatingFilesMixin(HashedFilesMixin):
    patterns = INTERPOLATION_PATTERNS


_compiled_interpolation_patterns: Dict[str, List[Tuple[re.Pattern, str]]] = _PureInterpolatingFilesMixin()._patterns


def serve_interpolated(request, path, *args, **kwargs):
    """
    This view extends the functionality of Django's ``serve()`` with the same as ``InterpolatingManifestStaticFilesStorage`` does.
    """
    response = serve(request, path, *args, **kwargs)
    if (isinstance(response, FileResponse) and request.path.startswith(settings.STATIC_URL)
            and fnmatchcase(path, INTERPOLATION_GLOB_PATTERN)):

        content = response.getvalue().decode()

        for extension, patterns in _compiled_interpolation_patterns.items():
            for pattern, template in patterns:

                def replace(match_obj: re.Match):
                    matches = match_obj.groupdict()
                    matches['url'] = InterpolatingManifestStaticFilesStorage.get_full_static_url(matches['url'])
                    return template % matches

                content = pattern.sub(replace, content)

        response.streaming_content = BytesIO(content.encode())

    return response
