from io import BytesIO
from pathlib import PurePosixPath

from django.contrib.staticfiles.storage import HashedFilesMixin, ManifestStaticFilesStorage
from django.contrib.staticfiles.utils import matches_patterns
from django.http import FileResponse
from django.templatetags.static import static
from django.views.static import serve


# In the files matching the glob patterns, the strings matching the regexes are replaced by the inner capturing group,
# which is first looked up in the static file manifest
INTERPOLATION_PATTERNS = (
    ('*.interpolated.*', (
        (
            r"""(?P<matched>\{% get_relative_static ["'](?P<url>.*?)["'] %\})""",
            "%(url)s",
        ),
    )),
)


class InterpolatingManifestStaticFilesStorage(ManifestStaticFilesStorage):
    """
    This class extends the functionality of ``ManifestStaticFilesStorage`` by replacing custom ``get_relative_static``
    tokens in files whose names end with ``.interpolated`` (not including the extension),  with the path of another static file.

    For example,
    ::
        {% get_relative_static './android-chrome-192x192.png' %}
    is replaced by
    ::
        ./android-chrome-192x192.edcbcb619832.png

    Development note: The paths have to be relative to the file, because of the way ``ManifestStaticFilesStorage`` works.
    """
    patterns = (
        *INTERPOLATION_PATTERNS,
        *ManifestStaticFilesStorage.patterns,
    )


class _PureInterpolatingFilesMixin(HashedFilesMixin):
    patterns = INTERPOLATION_PATTERNS


_compiled_interpolation_patterns = _PureInterpolatingFilesMixin()._patterns


def serve_interpolated(request, path, document_root=None, show_indexes=False):
    """
    This view extends the functionality of Django's ``serve()`` with the same as ``InterpolatingManifestStaticFilesStorage`` does.
    """
    response = serve(request, path, document_root=document_root, show_indexes=show_indexes)
    if (isinstance(response, FileResponse) and request.path.startswith("/static")
            and matches_patterns(path, _compiled_interpolation_patterns)):

        requested_path_static_dir = PurePosixPath(path).parent
        content = response.getvalue().decode()

        for extension, patterns in _compiled_interpolation_patterns.items():
            for pattern, template in patterns:

                def replace(match_obj):
                    _tag, relative_static_path = match_obj.groups()
                    registered_static_path = static(str(requested_path_static_dir / relative_static_path))
                    registered_relative_static_path = replace_filename(
                        relative_static_path, PurePosixPath(registered_static_path).name
                    )
                    return template % {'url': registered_relative_static_path}

                content = pattern.sub(replace, content)

        response.streaming_content = BytesIO(content.encode())

    return response


def replace_filename(path: str, new_filename: str):
    """
    Replaces the filename of the given ``path`` with ``new_filename``,
    keeping any relative path prefix (like ``./``).
    """
    directory, _filename, suffix = path.rpartition(PurePosixPath(path).name)
    return f"{directory}{new_filename}{suffix}"
