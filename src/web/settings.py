import copy
import logging
import sys
from importlib.util import find_spec
from pathlib import Path

import django.views.static
from django.conf.locale.en import formats as en_formats
from django.conf.locale.nb import formats as nb_formats
from django.utils.translation import gettext_lazy as _
from django_hosts import reverse_lazy

import env
from env import DatabaseSystem
from .static import serve_interpolated


is_testing = "test" in sys.argv
# Disable logging when testing
if is_testing:
    # Disable calls with severity level equal to or less than `CRITICAL` (i.e. everything)
    logging.disable(logging.CRITICAL)

# Build paths inside the project like this: BASE_DIR / ...
BASE_DIR = Path(__file__).resolve().parent.parent
REPO_DIR = BASE_DIR.parent
TESTS_DIR = BASE_DIR

# Make Django trust that the `X-Forwarded-Proto` HTTP header contains whether the request is actually over HTTPS,
# as the connection between Nginx (the proxy we're using) and Django (run by Channel's Daphne server) is currently always over HTTP
# (due to Daphne - seemingly - not supporting HTTPS)
# !!! WARNING: when deploying, make sure that Nginx always either overwrites or removes the `X-Forwarded-Proto` header !!!
# (see https://docs.djangoproject.com/en/stable/ref/settings/#secure-proxy-ssl-header)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Default values
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

DEBUG = env.DEBUG
SECRET_KEY = env.SECRET_KEY
ALLOWED_HOSTS = env.ALLOWED_HOSTS
INTERNAL_IPS = env.INTERNAL_IPS

STATIC_AND_MEDIA_FILES__PARENT_DIR = (  # (custom setting)
    REPO_DIR / env.STATIC_AND_MEDIA_FILES__PARENT_DIR
).resolve()
MEDIA_ROOT = STATIC_AND_MEDIA_FILES__PARENT_DIR / "media"
MEDIA_URL = "/media/"

# Based on https://github.com/Uninett/python-dataporten-auth/blob/bad1b95483c5da7d279df4a8d542a3c24c928095/src/demosite/settings.py#L120-L121
# "Client ID" in the OpenID Connect configuration in Feide's customer portal
SOCIAL_AUTH_DATAPORTEN_KEY = env.SOCIAL_AUTH_DATAPORTEN_KEY
# "Client Secret" in the same configuration
SOCIAL_AUTH_DATAPORTEN_SECRET = env.SOCIAL_AUTH_DATAPORTEN_SECRET

# These will be internationalized since `reverse_lazy()` is used
# (i.e. these will be English URLs when the user is on the English version of the website, and vice versa for Norwegian)
LOGIN_URL = reverse_lazy("login")
LOGIN_REDIRECT_URL = reverse_lazy("index_page")
LOGOUT_REDIRECT_URL = reverse_lazy("index_page")

CHECKIN_KEY = env.CHECKIN_KEY  # (custom setting)

# Converting MiB to bytes
FILE_MAX_SIZE = env.MEDIA_FILE_MAX_SIZE__MB * 2**20  # (custom setting)

# The `SESSION_COOKIE_DOMAIN`, `CSRF_COOKIE_DOMAIN` and `LANGUAGE_COOKIE_DOMAIN` will be set to this value
COOKIE_DOMAIN = env.COOKIE_DOMAIN  # (custom setting)
# The `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE` and `LANGUAGE_COOKIE_SECURE` will be set to this value
COOKIE_SECURE = env.COOKIE_SECURE  # (custom setting)

# For `django-hosts` to redirect correctly across subdomains, we have to specify the host we are running on.
PARENT_HOST = env.PARENT_HOST

IS_DEV_ENV = PARENT_HOST == "makentnu.dev"  # (custom setting)

EVENT_TICKET_EMAIL = "ticket@makentnu.no"  # (custom setting)


# When using more than one subdomain, the session cookie domain has to be set so that the subdomains can use the same session
# (Cannot use only ".localhost", as domains for cookies are required to have two dots in them)
SESSION_COOKIE_DOMAIN = COOKIE_DOMAIN
# Whether browsers may ensure that the session cookie is only sent under an HTTPS connection
SESSION_COOKIE_SECURE = COOKIE_SECURE
# The domain to be used when setting the CSRF cookie, which *must* start with a dot (.) to allow cross-subdomain POST/PUT/etc. requests
CSRF_COOKIE_DOMAIN = COOKIE_DOMAIN
# Whether browsers may ensure that the CSRF cookie is only sent under an HTTPS connection
CSRF_COOKIE_SECURE = COOKIE_SECURE
# The domain to use for the language cookie
LANGUAGE_COOKIE_DOMAIN = COOKIE_DOMAIN
# Whether browsers may ensure that the language cookie is only sent under an HTTPS connection
LANGUAGE_COOKIE_SECURE = COOKIE_SECURE

# The call to `find_spec()` returns something other than `None` only if `django-debug-toolbar` is installed
USE_DEBUG_TOOLBAR = DEBUG and find_spec("debug_toolbar") is not None  # (custom setting)

INSTALLED_APPS = [
    # `django-constance` should be listed before project apps (see https://django-constance.readthedocs.io/en/stable/#configuration)
    "constance",
    # App used for things regarding the whole project or across other apps
    # (Should be listed first, to be able to override things like management commands)
    "web.apps.WebConfig",
    # Should be listed before `django.contrib.staticfiles`
    # (see https://channels.readthedocs.io/en/stable/releases/4.0.0.html#decoupling-of-the-daphne-application-server)
    "daphne",
    # Built-in Django apps
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "web.apps.WebAdminConfig",  # Replaces 'django.contrib.admin'
    # Third-party packages with significant effect on Django's functionality
    "django_hosts",
    "channels",
    # Other third-party packages
    "social_django",
    "ckeditor",  # Must be listed after `web.apps.WebConfig` to make the custom `ckeditor/config.js` apply
    "ckeditor_uploader",
    "phonenumber_field",
    "simple_history",
    "sorl.thumbnail",
    # Project apps, listed alphabetically
    "announcements",
    "card",
    "checkin",
    "contentbox",
    "docs",
    "faq",
    "groups",
    "internal",
    "mail",
    "make_queue",
    "makerspace",
    "news",
    "users",
    "util",
    # Contains a lot of useful management commands, but is not strictly necessary for the project.
    # See this page for a list of all management commands: https://django-extensions.readthedocs.io/en/latest/command_extensions.html
    "django_extensions",
    *(["debug_toolbar"] if USE_DEBUG_TOOLBAR else []),
    # Should be placed last,
    # "to ensure that exceptions inside other apps' signal handlers do not affect the integrity of file deletions within transactions"
    "django_cleanup.apps.CleanupConfig",
]


MIDDLEWARE = [
    # Must be the first entry (see https://django-hosts.readthedocs.io/en/latest/#installation)
    "django_hosts.middleware.HostsRequestMiddleware",
    *(["debug_toolbar.middleware.DebugToolbarMiddleware"] if USE_DEBUG_TOOLBAR else []),
    # (See hints for ordering at https://docs.djangoproject.com/en/stable/ref/middleware/#middleware-ordering)
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "simple_history.middleware.HistoryRequestMiddleware",
    # Must be the last entry (see https://django-hosts.readthedocs.io/en/latest/#installation)
    "django_hosts.middleware.HostsResponseMiddleware",
]


ROOT_URLCONF = "web.urls"

# `django-hosts` configuration:
ROOT_HOSTCONF = "web.hosts"
DEFAULT_HOST = "main"
# All hosted subdomains - defined in `web/hosts.py`
ALL_SUBDOMAINS = (  # (custom setting)
    "i",
    "internal",
    "internt",
    "admin",
    "docs",
)


def generate_all_hosts(subdomains):
    return [PARENT_HOST, *[f"{subdomain}.{PARENT_HOST}" for subdomain in subdomains]]


# Tells `social-auth-core` (requirement of `python-social-auth`) to allow
# redirection to these host domains after logging in.
# (Undocumented setting; only found in this file:
# https://github.com/python-social-auth/social-core/blob/d66a2469609c7cfd6639b524981689db2f2d5540/social_core/actions.py#L22)
ALLOWED_REDIRECT_HOSTS = generate_all_hosts(ALL_SUBDOMAINS)


TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            BASE_DIR / "web/templates",  # For overriding Django admin templates
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "constance.context_processors.config",
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "web.context_processors.common_context_variables",
                "web.context_processors.login",
            ],
        },
    },
]

# TODO: should be removed when upgrading to Django 5.0 (see https://docs.djangoproject.com/en/4.1/releases/4.1/#forms)
FORM_RENDERER = "django.forms.renderers.DjangoDivFormRenderer"

ASGI_APPLICATION = "web.asgi.application"
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [(env.REDIS_HOST, env.REDIS_PORT)],
            # The maximum resend time of a message in seconds
            "expiry": 30,
            # The number of seconds before a connection expires
            "group_expiry": 900,
        },
    },
}

# Database
# https://docs.djangoproject.com/en/stable/ref/settings/#databases

match env.DATABASE_SYSTEM:
    case DatabaseSystem.POSTGRESQL:
        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.postgresql_psycopg2",
                "HOST": env.POSTGRES_HOST,
                "NAME": env.POSTGRES_DB_NAME,
                "USER": env.POSTGRES_DB_USER,
                "PASSWORD": env.POSTGRES_DB_PASSWORD,
            },
        }
    case DatabaseSystem.SQLITE:
        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": str((REPO_DIR / env.SQLITE_DB_PATH).resolve()),
            },
        }
    case _:
        raise NotImplementedError

# Password validation
# https://docs.djangoproject.com/en/stable/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

AUTH_USER_MODEL = "users.User"

# django-constance
CONSTANCE_BACKEND = "constance.backends.database.DatabaseBackend"
CONSTANCE_ADDITIONAL_FIELDS = {
    "url_field": [
        "django.forms.fields.URLField",
        {
            "max_length": 500,
            "widget": "django.forms.widgets.Textarea",
            "widget_kwargs": {
                "attrs": {"cols": 40, "rows": 2},
            },
        },
    ],
}
CONSTANCE_CONFIG = {
    "SHOW_APPLY_BUTTON_IN_HEADER_NAV": (
        True,
        _(
            "Determines whether the “Apply to MAKE” button in the navigation menu in the header is visible."
        ),
    ),
    "ENROLL_MEMBERS_GUIDE_LINK": (
        "",
        _("Link to the guide on what should be done when a new member enrolls."),
        "url_field",
    ),
    "RETIRE_MEMBERS_GUIDE_LINK": (
        "",
        _("Link to the guide on what should be done when a member retires."),
        "url_field",
    ),
    "QUIT_MEMBERS_GUIDE_LINK": (
        "",
        _("Link to the guide on what should be done when a member quits."),
        "url_field",
    ),
}
CONSTANCE_CONFIG_FIELDSETS = (
    (
        _("Main Site Settings"),
        ("SHOW_APPLY_BUTTON_IN_HEADER_NAV",),
    ),
    (
        _("Internal Site Settings"),
        (
            "ENROLL_MEMBERS_GUIDE_LINK",
            "RETIRE_MEMBERS_GUIDE_LINK",
            "QUIT_MEMBERS_GUIDE_LINK",
        ),
    ),
)

# Dataporten

USE_DATAPORTEN_AUTH = env.USE_DATAPORTEN_AUTH  # (custom setting)

SOCIAL_AUTH_DATAPORTEN_FEIDE_SSL_PROTOCOL = True
SOCIAL_AUTH_LOGIN_REDIRECT_URL = reverse_lazy("index_page")
SOCIAL_AUTH_NEW_USER_REDIRECT_URL = reverse_lazy("index_page")
SOCIAL_AUTH_REDIRECT_IS_HTTPS = True

# This URL is the value of the `end_session_endpoint` key from https://auth.dataporten.no/.well-known/openid-configuration
# (see https://docs.feide.no/service_providers/manage/openid_connect/redir_etter_logout.html)
DATAPORTEN_LOGOUT_URL = (  # (custom setting)
    "https://auth.dataporten.no/openid/endsession"
)

# The following code is based on
# https://github.com/Uninett/python-dataporten-auth/blob/bad1b95483c5da7d279df4a8d542a3c24c928095/src/demosite/settings.py#L111-L127

AUTHENTICATION_BACKENDS = (
    # 'dataporten.social.DataportenFeideOAuth2',
    # 'dataporten.social.DataportenEmailOAuth2',
    "dataporten.social.DataportenOAuth2",
    "django.contrib.auth.backends.ModelBackend",
)

SOCIAL_AUTH_ADMIN_USER_SEARCH_FIELDS = ["username", "first_name", "email"]

SOCIAL_AUTH_DATAPORTEN_EMAIL_KEY = SOCIAL_AUTH_DATAPORTEN_KEY
SOCIAL_AUTH_DATAPORTEN_EMAIL_SECRET = SOCIAL_AUTH_DATAPORTEN_SECRET

SOCIAL_AUTH_DATAPORTEN_FEIDE_KEY = SOCIAL_AUTH_DATAPORTEN_KEY
SOCIAL_AUTH_DATAPORTEN_FEIDE_SECRET = SOCIAL_AUTH_DATAPORTEN_SECRET

# Internationalization
# https://docs.djangoproject.com/en/stable/topics/i18n/

LANGUAGE_CODE = "nb"

LANGUAGES = (
    ("nb", "Norsk"),
    ("en", "English"),
)

LOCALE_PATHS = [
    BASE_DIR / "locale",
]

TIME_ZONE = "Europe/Oslo"

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Set time format for English to match the Norwegian format
for format_name in ("TIME_FORMAT", "DATETIME_FORMAT", "SHORT_DATETIME_FORMAT"):
    format_str: str = getattr(en_formats, format_name)
    setattr(en_formats, format_name, format_str.replace("P", "H:i"))

nb_formats.DECIMAL_SEPARATOR = "."


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/stable/howto/static-files/

STATIC_ROOT = STATIC_AND_MEDIA_FILES__PARENT_DIR / "static"
STATIC_URL = "/static/"

# This is based on Django's ManifestStaticFilesStorage, which appends every static file's MD5 hash to its filename,
# which avoids waiting for browsers' cache to update if a file's contents change
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "web.static.ManifestStaticFilesStorage",
    },
}
# Ignores adding a hash to the files whose paths match these glob patterns:
# NOTE: Ignored files should be named so that it's obvious that they should be renamed when their contents update,
#       to avoid being "stuck" in browsers' cache - which is what `ManifestStaticFilesStorage` would have prevented
#       if the files were not ignored.
#       For example: placing ignored files inside a folder with a version number as its name.
MANIFEST_STATICFILES_IGNORE_PATTERNS = [  # (custom setting)
    "ckeditor/mathjax/*",
]
# Monkey patch view used for serving static files (for development only; Nginx is used in production)
django.views.static.serve = serve_interpolated


# Code taken from https://github.com/django-ckeditor/django-ckeditor/issues/404#issuecomment-687778492
def static_lazy(path):
    from django.templatetags.static import static
    from django.utils.functional import lazy

    return lazy(lambda: static(path), str)()


CKEDITOR_UPLOAD_PATH = "ckeditor_upload/"
CKEDITOR_IMAGE_BACKEND = "ckeditor_uploader.backends.PillowBackend"

# Group files by directories when browsing uploaded files
CKEDITOR_BROWSE_SHOW_DIRS = True
CKEDITOR_FILENAME_GENERATOR = "util.ckeditor_utils.get_filename"
# Don't place uploaded files in directories per date (placement is decided in `ckeditor_utils.py`)
CKEDITOR_RESTRICT_BY_DATE = False

CKEDITOR_CONFIGS = {
    "default": {
        "skin": "moono-lisa",
        "toolbar_main": [
            {"name": "editing", "items": ["Find"]},
            {
                "name": "basicstyles",
                "items": [
                    "Bold",
                    "Italic",
                    "Underline",
                    "Strike",
                    "Subscript",
                    "Superscript",
                ],
            },
            {"name": "colors", "items": ["TextColor", "BGColor"]},
            {"name": "format", "items": ["Format", "Styles", "RemoveFormat"]},
            "/",
            {
                "name": "paragraph",
                "items": [
                    "NumberedList",
                    "BulletedList",
                    "Blockquote",
                    "-",
                    "Outdent",
                    "Indent",
                    "-",
                    "JustifyLeft",
                    "JustifyCenter",
                    "JustifyRight",
                    "JustifyBlock",
                ],
            },
            {"name": "links", "items": ["Link", "Unlink", "Anchor"]},
            {
                "name": "insert",
                "items": ["Mathjax", "CodeSnippet", "HorizontalRule", "-", "Image"],
            },
        ],
        "toolbar": "main",
        # All MathJax files downloaded from https://github.com/mathjax/MathJax/tree/2.7.9
        "mathJaxLib": static_lazy(
            "ckeditor/mathjax/v2.7.9/MathJax.js?config=TeX-AMS_HTML"
        ),
        "tabSpaces": 4,
        "contentsCss": [
            static_lazy("web/css/font_faces.css"),
            static_lazy("ckeditor/ckeditor/customstyles.css"),
            static_lazy("ckeditor/ckeditor/contents.css"),  # CKEditor's default styles
        ],
        "extraPlugins": ",".join(
            [
                "mathjax",
                "codesnippet",
                "uploadimage",
                "image2",
            ]
        ),
    }
}
# This config should only be used for a rich text widget if the user has the `internal.can_change_rich_text_source` permission
CKEDITOR_EDIT_SOURCE_CONFIG_NAME = "edit_source"  # (custom setting)
CKEDITOR_CONFIGS[CKEDITOR_EDIT_SOURCE_CONFIG_NAME] = copy.deepcopy(
    CKEDITOR_CONFIGS["default"]
)
CKEDITOR_CONFIGS[CKEDITOR_EDIT_SOURCE_CONFIG_NAME]["toolbar_main"].append(
    {"name": "editsource", "items": ["Source"]}
)

# Phonenumbers
PHONENUMBER_DEFAULT_REGION = "NO"
PHONENUMBER_DEFAULT_FORMAT = "INTERNATIONAL"

# See https://django-simple-history.readthedocs.io/en/stable/historical_model.html#filefield-as-a-charfield
SIMPLE_HISTORY_FILEFIELD_TO_CHARFIELD = True


if USE_DEBUG_TOOLBAR:
    DEBUG_TOOLBAR_CONFIG = {
        "RENDER_PANELS": False,
        "DISABLE_PANELS": {
            # 'debug_toolbar.panels.history.HistoryPanel',
            "debug_toolbar.panels.versions.VersionsPanel",
            # 'debug_toolbar.panels.timer.TimerPanel',
            # 'debug_toolbar.panels.settings.SettingsPanel',
            # 'debug_toolbar.panels.headers.HeadersPanel',
            # 'debug_toolbar.panels.request.RequestPanel',
            "debug_toolbar.panels.sql.SQLPanel",
            "debug_toolbar.panels.staticfiles.StaticFilesPanel",
            "debug_toolbar.panels.templates.TemplatesPanel",
            "debug_toolbar.panels.cache.CachePanel",
            "debug_toolbar.panels.signals.SignalsPanel",
            # 'debug_toolbar.panels.logging.LoggingPanel',
            "debug_toolbar.panels.redirects.RedirectsPanel",
            "debug_toolbar.panels.profiling.ProfilingPanel",
        },
    }


# Emailing
PRINT_EMAILS_TO_CONSOLE = DEBUG or is_testing  # (custom setting)
EMAIL_HOST = env.EMAIL_HOST
EMAIL_HOST_USER = env.EMAIL_HOST_USER
EMAIL_PORT = env.EMAIL_PORT
EMAIL_USE_TLS = env.EMAIL_USE_TLS
DEFAULT_FROM_EMAIL = env.DEFAULT_FROM_EMAIL
SERVER_EMAIL = env.SERVER_EMAIL
EMAIL_SUBJECT_PREFIX = env.EMAIL_SUBJECT_PREFIX
ADMINS = env.ADMINS

# See https://docs.djangoproject.com/en/stable/topics/logging/ for
# more details on how to customize your logging configuration.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "{message}",
            "style": "{",
        },
        "verbose": {
            "format": "{levelname}\t| {name}\t|\t{message}",
            "style": "{",
        },
    },
    "filters": {
        "require_debug_false": {
            "()": "django.utils.log.RequireDebugFalse",
        },
        "require_debug_true": {
            "()": "django.utils.log.RequireDebugTrue",
        },
    },
    "handlers": {
        "mail_admins": {
            "level": "ERROR",
            "filters": ["require_debug_false"],
            "class": "django.utils.log.AdminEmailHandler",
        },
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "standard",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": True,
        },
        "django.request": {
            "handlers": ["mail_admins"],
            "level": "ERROR",
            "propagate": True,
        },
        **{
            f"django.{disabled_logger_name}": {"propagate": False}
            for disabled_logger_name in ["db", "template", "utils"]
        },
        # Prevent deluge of "X of X channels over capacity in group stream_XXX" INFO messages from `channels_redis`
        "channels_redis": {
            "handlers": ["console"],
            "level": "WARNING",
        },
    },
}

"""
Uncomment to print all database queries to the console;
useful for checking e.g. that a request doesn't query the database more times than necessary.
"""
# LOGGING["loggers"]["django.db"] = {
#     "level": "DEBUG",
#     "propagate": True,
# }
