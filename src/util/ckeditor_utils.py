"""
Code based on https://github.com/xcom-data/xcom/blob/b2c51ce07f9f33e16742a61bd9e3d96f0683a317/xcom/util/ckeditor_utils.py
"""
from typing import Type
from urllib.parse import unquote, urlparse

from ckeditor_uploader import utils
from django.conf import settings
from django.db.models import Model
from django.urls import resolve
from django.utils import timezone
from django.utils.text import slugify

from docs.models import Page
from util.locale_utils import localize_lazy_string
from util.logging_utils import log_request_exception
from web import admin_urls


def get_filename(upload_name: str, request):
    """
    This function is used by the ``CKEDITOR_FILENAME_GENERATOR`` setting
    to set the name (incl. prefixed names of containing folders) of files uploaded using the CKEditor uploader widget.
    """
    filename = utils.slugify_filename(upload_name)
    date_prefix = timezone.localdate().strftime("%Y/%m/%d")

    try:
        folder_name = get_folder_name(request)
    except Exception as e:
        log_request_exception(f"Failed to determine the proper folder name for the file with name '{upload_name}'", e, request)
        # Fall back to the default date-prefixed format
        return f"{date_prefix}/{filename}" if should_prefix_date() else filename

    return f"{folder_name}/{date_prefix}/{filename}"


def get_folder_name(request):
    http_headers = request.headers
    origin_full_url = http_headers.get('REFERER')  # REFERER is supposed to have a typo
    if not origin_full_url:
        raise Exception("Could not find HTTP_REFERER among the request's headers")

    origin_path = urlparse(origin_full_url).path
    # Replace `%xx` escapes with their single-character equivalent, to prevent errors in `resolve()` below
    # - which could happen if resolving e.g. the path of a documentation page, which can contain `%xx` characters (like `%20` for space)
    origin_path = unquote(origin_path)

    view_func, _args, _kwargs = resolve(origin_path, request.urlconf)
    # If the URL config is the one for the Django admin subdomain:
    if request.urlconf == admin_urls.__name__:
        # The view must be a `ModelAdmin` subclass
        model: Type[Model] = view_func.model_admin.model
    else:
        # The view is (probably) a `SingleObjectMixin` subclass
        model: Type[Model] = view_func.view_class.model

    model_name_plural = get_model_name_plural(model)
    return slugify(model_name_plural).replace("-", "_")  # The naming convention for folders is snake_case


def get_model_name_plural(model: Type[Model]):
    if model == Page:
        return "docs"

    return localize_lazy_string(model._meta.verbose_name_plural, language_code="en")


def should_prefix_date():
    # If not grouping uploaded files by date, do it anyway, manually;
    # otherwise, the filename should already be date-prefixed
    return not getattr(settings, 'CKEDITOR_RESTRICT_BY_DATE', True)
